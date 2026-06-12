# E5P Display: Vertical Shift + Color Rotation - Root Cause & Fix

**Status: FIXED (2026-06-11).** Zero shift, correct colors, verified with a
calibration pattern at panel level (screenshots can't see this class of bug -
they capture the composited buffer, not what the panel latches).

## Symptoms

- Whole UI shifted up by a constant number of lines; the overflowing top part
  wrapped in from the bottom.
- Sometimes additionally R→B→G→R color channel rotation.
- Composited screenshots (grim) looked perfect - defect existed only on glass.
- Shift amount was immune to porch changes, EOT/HSE flags, VOP re-phasing.
  Observed lock states: 35 lines (= vsa 4 + vbp 31) and 120 lines.

## Defect model

The panel stream was offset by `N whole lines ± 1 byte` at the DDIC
(Orise OTM1287A-class, init unlock `FF 12 84 01`). The ±1 byte IS the color
rotation: RGB888 bytes land one byte off → channels rotate. Line shift and
color rotation were one defect with two faces. The DDIC latches its frame
origin ONCE around video-mode start / last init command and never re-syncs
(proven: re-arming the DSI video engine with VOP parked changed nothing).

## Why Android worked

Reverse engineering the stock firmware (`uboot.img`, `boot.img`, resource
image) showed the entire working stack avoids the problem rather than solving
it at kernel level:

1. **Vendor U-Boot 2017.09 brings the display up** (draws 720x1280 logo.bmp
   from the resource partition; uses the kernel DTB via
   `CONFIG_USING_KERNEL_DTB` - its own DTB has no display nodes).
2. **BSP kernel 4.19.232 does a smooth handover** (`route-dsi0` +
   `drm-logo` reserved memory): it never re-initializes the panel at boot.
3. The JELOS MOD / plumOS community images reuse vendor U-Boot + BSP kernel
   (their DT is `rockchip,rk3566-rk817-tablet` with route/logo nodes), so they
   inherit the same working bring-up. **Nobody ran a mainline display stack on
   this panel before this port.**

## What actually fixed it

Stop theorizing; clone the working configuration. Boot stock Android (eMMC),
then:

```
adb root
adb shell cat /sys/kernel/debug/regmap/fe060000.dsi-host/registers   # BSP regmap debugfs
adb shell cat /sys/kernel/debug/regmap/fe850000.video-phy/registers
```

Dumps archived in `docs/data/android_dsi_regs.txt` / `android_phy_regs.txt`.
Diff against ROCKNIX (`devmem` loop over 0xfe060000..0xfc) and erase every
difference:

| Item | Android | ROCKNIX before | Fix |
|---|---|---|---|
| Lane rate | **432 Mbps exactly** (derived from lbcc regs 0x48/0x4c/0x50) | 487.5 | dts `rockchip,lane-rate = <432>` + kernel support for the BSP-style DT prop (recomputes the full D-PHY config, not just hs_clk) |
| Host/PHY rate consistency | consistent | host calc 433 vs PHY 487.5 at one point | host calc kept at mainline 10/8; mismatch was THE color-rotation cause |
| VID_MODE_CFG (0x38) | 0xBF02 (LP_CMD_EN set) | 0x3F02 | `val = ENABLE_LOW_POWER \| ENABLE_LOW_POWER_CMD` |
| PCKHDL_CFG (0x2c) | 0x1C (no EOT) | 0x1D | panel flags 0x813 → **0xa03** (drop HSE, add NO_EOT) |
| PHY_TMR_CFG (0x9c) | 0x14102710 (BSP constants) | computed 0x163B2710 | fixed write hs2lp=0x14 lp2hs=0x10 maxrd=10000 |
| PHY_TMR_LPCLK (0x98) | 0x00400040 | computed 0x001F0049 | fixed write 0x40/0x40 |
| Last DCS command (GEN_HDR 0x6c) | 0x2905 (display-on) | 0x1105 (**sleep-out!**) | gate the generic-dsi driver's post-init `display_on + exit_sleep` resend (reversed order!) behind new DT prop `rocknix,no-post-init-cmds` |

Remaining diffs after fix - all benign: 0x4c lbcc ±1 (rounding), 0x68
CMD_MODE_CFG (command LP/HS routing), 0xa0 bit3 (forcepll), 0xc0 bit7.

Additionally kept (BSP behavior, properly latched): VOP2 VP0 standby bracket
around DSI enable in `dw-mipi-dsi.c`. NOTE: VOP2 registers are SHADOWED -
any direct write (including the standby bit at 0xfe040c00 bit31) is a NO-OP
until `0x8001` is written to REG_CFG_DONE (0xfe040000). Our first quirk
version silently did nothing because of this.

## Files / persistence

- `dts/rk3566-e5p.dts` - lane-rate, flags 0xa03, `rocknix,no-post-init-cmds`,
  stock C0 init line (`c00064000e1200640e12` - do not "experiment" with C0:
  any deviation moves the lock to the worse 120-line state).
- `kernel/0101-e5p-display-android-parity.patch` - dw-mipi-dsi.c +
  dw-mipi-dsi-rockchip.c changes; copy into
  `projects/Rockchip/devices/RK3566/patches/linux/` in the build tree.
- `kernel/panel-generic-dsi.c` - gated post-init resend; replaces
  `packages/linux-drivers/generic-dsi/sources/panel-generic-dsi.c`.
- `docs/data/android_dsi_regs.txt`, `docs/data/rocknix_dsi_regs_fixed.txt`,
  `docs/data/android_phy_regs.txt` - register dumps (ground truth).

## Hard-won debugging lessons

- **adb + BSP regmap debugfs is the ground truth machine.** One register diff
  beat a week of single-variable experiments.
- grim screenshots show the composited buffer only; panel-level corruption
  needs eyes on glass + a calibration pattern (`swayimg -f --scale=fit`,
  swaybg can't decode PNGs in this image).
- Two confounds poisoned early experiments: stale dtb installs
  (docker cp leaves root-owned files → make silently keeps the old dtb;
  `chown builder + touch` then verify via `strings dtb | grep <token>`) and
  the host-433/PHY-487.5 rate mismatch.
- Sync-pulse mode (flags 0x805) = black screen; this panel is burst-only.
- Device clock: `last mount time in the future` from e2fsck is normal (no RTC).
