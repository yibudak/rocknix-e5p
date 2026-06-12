# WiFi Bring-Up Notes

## Status

WiFi is verified on hardware through an out-of-tree Realtek RTL8733BS SDIO
vendor driver. The driver is integrated as a ROCKNIX kernel-module package;
network configuration is owned by ROCKNIX's normal network manager
(NetworkManager with the iwd backend on current images).

Verified runtime state:

- SDIO ID: `024C:B733`
- Driver/module: `8733bs`
- Interface: `wlan0`
- `ip link set wlan0 up`: OK
- `iw dev wlan0 scan`: OK
- Association on both 2.4 GHz and 5 GHz: OK (dual-band 1T1R; ~150 Mbit
  link rate at 40 MHz on 5 GHz)
- Static development IP: OK
- SSH over WiFi: OK

During bring-up the module was copied into the writable kernel overlay on the
running device. That overlay path is now considered legacy debug state.

## What the Chip Actually Is

The stock/live DTS suggested `wifi_chip_type = "ap6255"`, which points toward a
Broadcom module. That was misleading for the tested hardware.

The running ROCKNIX kernel reported the SDIO function as:

```text
SDIO_ID=024C:B733
MODALIAS=sdio:c07v024CdB733
```

This ID matches Realtek RTL8733BS. The `8733bs` vendor driver also advertises:

```text
alias: sdio:c07v024CdB733*
alias: sdio:c07v024CdB73A*
```

## Failed Driver Attempts

These were tested and rejected:

- `brcmfmac`: wrong family for `024C:B733`; loads from ROCKNIX config but does
  not bind usefully.
- staging `r8723bs`: can be patched to bind `024C:B733`, but it is the wrong
  chip family. `wlan0` appears, then `ip link set wlan0 up` fails because
  `_InitPowerOn_8723BS` fails.
- mainline `rtw88_8723cs` patched for `024C:B733`: firmware loads, then MAC
  power-on fails with `failed to poll offset=0x5 ... mac power on failed`.
- mainline `rtw88_8723ds` patched for `024C:B733`: same MAC power-on failure.

## Working Driver

The verified source during bring-up was:

```text
https://github.com/newbie-461/RTL8733BS_WiFi_linux_v5.14.1.1-46
```

The driver needed Linux 6.12 compatibility fixes. They are applied by the
ROCKNIX package from:

```text
packages/kernel/drivers/RTL8733BS/patch_rtl8733bs_612.py
```

The important API updates were:

- `complete_and_exit()` -> `kthread_complete_and_exit()`
- `prandom_u32()` -> `get_random_u32()`
- `strlcpy()` -> `strscpy()`
- `netif_napi_add()` -> `netif_napi_add_weight()`
- cfg80211 MLO-era callback signature updates
- `PDE_DATA()` -> `pde_data()`
- guard removed `REGULATORY_IGNORE_STALE_KICKOFF`

## Build Integration

The durable image path is the `RTL8733BS` kernel driver package in the ROCKNIX
tree:

```text
packages/kernel/drivers/RTL8733BS/package.mk
```

RK3566 builds select it through:

```text
projects/Rockchip/devices/RK3566/options
```

To rebuild just this driver inside the ROCKNIX build container:

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build RTL8733BS'
```

Expected output:

```text
/lib/modules/6.12.17/kernel/drivers/net/wireless/8733bs.ko
```

Check metadata:

```bash
modinfo 8733bs.ko | grep -E 'filename|version|alias:.*B733|depends|vermagic'
```

## Live-Test on Device

Copy the module:

```bash
scp /tmp/rtl8733bs/8733bs.ko root@<device-ip>:/storage/.cache/e5p-test/8733bs.ko
```

Load and scan:

```bash
ssh root@<device-ip> '
  systemctl stop connman connman-vpn wpa_supplicant 2>/dev/null || true
  modprobe -r r8723bs brcmfmac brcmutil rtw88_8723cs rtw88_8723ds \
    rtw88_8703b rtw88_8723d rtw88_8723x rtw88_sdio rtw88_core mac80211 2>/dev/null || true
  modprobe cfg80211
  insmod /storage/.cache/e5p-test/8733bs.ko rtw_drv_log_level=4
  sleep 5
  ip link set wlan0 up
  iw dev wlan0 scan | sed -n "1,120p"
'
```

## Network Management

Use the ROCKNIX WiFi UI for association, DHCP, static IP, and DNS. Do not add
device-specific helper services; they fight the system network manager and can
leave the system in a half-configured state.

For development, USB networking should also be left to ROCKNIX's built-in
`usbgadget` setup. Custom watchdog services were useful while the driver was
unknown, but they are not part of the port.

## Legacy Runtime Overlay

The manual overlay and direct `wpa_supplicant` commands above are kept only as
bring-up notes. Use them for low-level driver debugging only, then restore
ConnMan before normal testing.

---

## 2026-06 update: NetworkManager+iwd era (20260601 base) - SAE fix

ConnMan is gone; the image uses NetworkManager with the iwd backend. The
WPA3-transition failure resurfaced there and is now FIXED at the driver:

- Symptom: ES "network error" on WPA3-transition (WPA2/WPA3 mixed) APs.
  iwd journal: `FullMAC driver: rtl8733bs using SAE. Expect EXTERNAL_AUTH` →
  `connect-failed, status: 1`, forever. Pure-WPA2 APs unaffected.
- Root cause: driver advertises `NL80211_FEATURE_SAE` but the FullMAC SAE
  path never completes association. iwd sees the flag and insists on SAE.
- Fix (fix 7 in `scripts/patch_rtl8733bs_612.py`): drop the SAE feature flag
  in `os_dep/linux/ioctl_cfg80211.c` → iwd falls back to WPA2-PSK → connects.
- Patch-script gotcha fixed at the same time: `patch()` now checks `new in
  text` BEFORE replacing - the set_txpower pattern is a substring of its own
  replacement and a rerun used to double-apply it (duplicate `radio_idx`,
  build break).
- The fix is applied at build time by the patch script, so images built from
  this tree ship the fixed module; no runtime workaround is needed.
- Seeding pattern for a new network when the device has no working WiFi yet:
  write a NetworkManager keyfile (system-connections) onto the SD STORAGE
  partition from another machine, then boot - NM picks it up.
