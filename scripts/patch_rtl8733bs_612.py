#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""
Patch the out-of-tree Realtek RTL8733BS vendor driver for ROCKNIX's
Linux 6.12.17 kernel.

The verified source tree during bring-up was:
  https://github.com/newbie-461/RTL8733BS_WiFi_linux_v5.14.1.1-46

The script is idempotent for the edits it knows about.
"""

from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()


def patch(path: str, replacements: list[tuple[str, str]]) -> None:
    p = ROOT / path
    text = p.read_text()
    original = text
    for old, new in replacements:
        # check `new` FIRST: when `old` is a substring of `new` (e.g. the
        # set_txpower radio_idx insertion), replacing again would double-apply
        if new in text:
            continue
        if old in text:
            text = text.replace(old, new)
        else:
            raise SystemExit(f"missing pattern in {p}: {old!r}")
    if text != original:
        p.write_text(text)
        print(f"patched {p}")
    else:
        print(f"already patched {p}")


patch(
    "os_dep/osdep_service.c",
    [
        ("\tcomplete_and_exit(comp, 0);", "\tkthread_complete_and_exit(comp, 0);"),
        ("return prandom_u32();", "return get_random_u32();"),
    ],
)

patch(
    "os_dep/linux/os_intfs.c",
    [
        ("strlcpy(", "strscpy("),
        (
            "netif_napi_add(ndev, &adapter->napi, rtw_recv_napi_poll, RTL_NAPI_WEIGHT);",
            "netif_napi_add_weight(ndev, &adapter->napi, rtw_recv_napi_poll, RTL_NAPI_WEIGHT);",
        ),
    ],
)

patch(
    "include/osdep_service_linux.h",
    [
        (
            "#if (defined(__ANDROID_COMMON_KERNEL__) && (LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 41)))",
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6, 12, 0)) || (defined(__ANDROID_COMMON_KERNEL__) && (LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 41)))",
        ),
    ],
)

patch(
    "os_dep/linux/ioctl_cfg80211.c",
    [
        (
            "cfg80211_ch_switch_started_notify(adapter->pnetdev, &chdef, 0, false);",
            "cfg80211_ch_switch_started_notify(adapter->pnetdev, &chdef, 0, 0, false);",
        ),
        (
            "static int cfg80211_rtw_change_beacon(struct wiphy *wiphy, struct net_device *ndev,\n\t\tstruct cfg80211_beacon_data *info)\n{\n\tint ret = 0;",
            "static int cfg80211_rtw_change_beacon(struct wiphy *wiphy, struct net_device *ndev,\n\t\tstruct cfg80211_ap_update *ap_update)\n{\n\tstruct cfg80211_beacon_data *info = &ap_update->beacon;\n\tint ret = 0;",
        ),
    ],
)

patch(
    "os_dep/linux/wifi_regd.c",
    [
        (
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 19, 0))\n\twiphy->regulatory_flags |= REGULATORY_IGNORE_STALE_KICKOFF;\n#endif",
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 19, 0)) && defined(REGULATORY_IGNORE_STALE_KICKOFF)\n\twiphy->regulatory_flags |= REGULATORY_IGNORE_STALE_KICKOFF;\n#endif",
        ),
    ],
)

patch(
    "os_dep/linux/rtw_proc.c",
    [
        ("PDE_DATA(", "pde_data("),
    ],
)


# Kernel 7.0 dropped support for the ancient EXTRA_CFLAGS kbuild variable,
# so none of the driver Makefile -I/-D flags reach the compiler
# (first symptom: fatal error: drv_types.h: No such file or directory).
# Bridge it: ccflags-y is recursively expanded, so a single += at the end
# of the Makefile picks up every EXTRA_CFLAGS accumulated above it.
_mk = ROOT / "Makefile"
_text = _mk.read_text()
if "ccflags-y += $(EXTRA_CFLAGS)" not in _text:
    _mk.write_text(_text + "\nccflags-y += $(EXTRA_CFLAGS)\n")
    print(f"patched {_mk} (ccflags-y bridge)")
else:
    print(f"already patched {_mk} (ccflags-y bridge)")


# Kernel 7.0 includes the external-module Makefile with $(src) undefined,
# and the driver Makefile freezes EXTRA_CFLAGS with := while expanding
# -I$(src)/include, producing dead "-I/include" paths. Pin src to the
# module directory before anything expands it.
_src_guard = (
    "# kernel 7.0: $(src) is no longer set for external modules\n"
    "ifeq ($(src),)\n"
    "src := $(or $(KBUILD_EXTMOD),$(M),$(CURDIR))\n"
    "endif\n\n"
)
_text = _mk.read_text()
if "src := $(or $(KBUILD_EXTMOD)" not in _text:
    _mk.write_text(_src_guard + _text)
    print(f"patched {_mk} (src guard)")
else:
    print(f"already patched {_mk} (src guard)")


# The "ANDROID COMMON KERNEL" block rewrites every relative -I to an
# absolute path IF the same dir exists under $(srctree) - and the kernel
# tree has its own include/, so the driver -I$(src)/include gets hijacked
# to the kernel include dir. Compilation runs with cwd = module dir, so
# the relative paths are fine as-is; disable the block.
patch(
    "Makefile",
    [
        (
            "# Convert to absolute path\nifneq ($(srctree),)",
            "# Convert to absolute path (disabled: hijacks -I$(src)/include on kernel 7.0)\nifneq (,)",
        ),
    ],
)


# Kernel 6.15/6.16 removed the legacy timer API that 7.0 no longer carries:
# from_timer() -> timer_container_of(), del_timer(_sync)() -> timer_delete(_sync)().
# Every driver TU includes osdep_service_linux.h, so shim them there once.
patch(
    "include/osdep_service_linux.h",
    [
        (
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(4, 14, 0))\nstatic inline void timer_hdl(struct timer_list *in_timer)",
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0))\n"
            "#ifndef from_timer\n"
            "#define from_timer(var, callback_timer, timer_fieldname) \\\n"
            "\ttimer_container_of(var, callback_timer, timer_fieldname)\n"
            "#endif\n"
            "#ifndef del_timer_sync\n"
            "#define del_timer_sync(t) timer_delete_sync(t)\n"
            "#endif\n"
            "#ifndef del_timer\n"
            "#define del_timer(t) timer_delete(t)\n"
            "#endif\n"
            "#endif\n\n"
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(4, 14, 0))\nstatic inline void timer_hdl(struct timer_list *in_timer)",
        ),
    ],
)


# Kernel 7.0 exports its own hmac_sha256() from <crypto/sha2.h> with a
# different signature. The driver-local copy is unused (callers use the
# _vector variant), so rename it out of the way.
patch(
    "core/crypto/sha256.h",
    [
        ("int hmac_sha256(const u8 *key", "int rtw_hmac_sha256(const u8 *key"),
    ],
)
patch(
    "core/crypto/sha256.c",
    [
        ("int hmac_sha256(const u8 *key", "int rtw_hmac_sha256(const u8 *key"),
    ],
)


# cfg80211 ops grew radio_idx/link_id/netdev parameters by kernel 7.0:
#   set_wiphy_params(wiphy, radio_idx, changed)
#   set_tx_power(wiphy, wdev, radio_idx, type, mbm)
#   get_tx_power(wiphy, wdev, radio_idx, link_id, dbm)
#   set_monitor_channel(wiphy, dev, chandef)
patch(
    "os_dep/linux/ioctl_cfg80211.c",
    [
        (
            "static int cfg80211_rtw_set_wiphy_params(struct wiphy *wiphy, u32 changed)",
            "static int cfg80211_rtw_set_wiphy_params(struct wiphy *wiphy, int radio_idx, u32 changed)",
        ),
        (
            "static int cfg80211_rtw_set_txpower(struct wiphy *wiphy,\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\tstruct wireless_dev *wdev,\n#endif\n",
            "static int cfg80211_rtw_set_txpower(struct wiphy *wiphy,\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\tstruct wireless_dev *wdev,\n#endif\n\tint radio_idx,\n",
        ),
        (
            "static int cfg80211_rtw_get_txpower(struct wiphy *wiphy,\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\tstruct wireless_dev *wdev,\n#endif\n\tint *dbm)",
            "static int cfg80211_rtw_get_txpower(struct wiphy *wiphy,\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\tstruct wireless_dev *wdev,\n#endif\n\tint radio_idx, unsigned int link_id,\n\tint *dbm)",
        ),
        (
            "static int cfg80211_rtw_set_monitor_channel(struct wiphy *wiphy\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\t, struct cfg80211_chan_def *chandef",
            "static int cfg80211_rtw_set_monitor_channel(struct wiphy *wiphy\n\t, struct net_device *mon_ndev\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(3, 8, 0))\n\t, struct cfg80211_chan_def *chandef",
        ),
    ],
)

# Fix 7: never advertise SAE. The FullMAC firmware's SAE/external-auth path
# always fails association (status 1), so WPA3-transition (WPA2/WPA3 mixed)
# APs can never connect: iwd sees NL80211_FEATURE_SAE and
# insists on SAE. Dropping the flag makes iwd fall back to WPA2-PSK, which
# works on both bands. Verified on hardware 2026-06-11/21.
patch(
    "os_dep/linux/ioctl_cfg80211.c",
    [
        (
            "#if (KERNEL_VERSION(3, 8, 0) <= LINUX_VERSION_CODE)\n\twiphy->features |= NL80211_FEATURE_SAE;\n#endif",
            "#if (KERNEL_VERSION(3, 8, 0) <= LINUX_VERSION_CODE)\n\t/* SAE disabled: iwd+fullMAC SAE assoc fails on 8733bs */;\n#endif",
        ),
    ],
)
