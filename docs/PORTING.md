# Porting Notes: How This Port Works

Technical background for developers. For user-facing info, see the
[README](../README.md).

## Why this port exists

Previous community efforts to run Linux on the E5 Plus (e.g. JELOS mods)
failed because of an **incorrect regulator node** in the device tree:

| ❌ Wrong (Powkiddy X55) | ✅ Correct (E5 Plus) |
|:--|:--|
| `tcs4525 @ i2c0 0x1c` | `silergy,syr827 @ i2c0 0x40` |

The E5 Plus shares the RK3566 SoC with the Powkiddy X55 but uses a different
CPU regulator, a different panel, and different volume-key wiring. Nobody had
run a mainline display stack on this panel before this port.

## Key fixes

### `kernel/panel-e5p.c` - DRM panel driver
- Replays the exact 112-command DCS initialization sequence captured from
  stock Android.
- Compatible string: `gamemt,e5p-panel`.
- Based on mainline `panel-himax-hx8394.c`.

### `kernel/0101-e5p-display-android-parity.patch` - display pipeline
- The panel DDIC latches its frame origin once at video-mode start; any
  mismatch with the stock register configuration shows up as a permanent
  line shift and/or color-channel rotation.
- Fixed by diffing live DSI/PHY registers against stock Android and erasing
  every difference (lane rate 432 Mbps, LP command mode, EOT/HSE flags, PHY
  timer constants). Full forensic write-up in [DISPLAY.md](DISPLAY.md).

### `dts/rk3566-e5p.dts` - device tree
- Critical fix: `vdd_cpu` → `silergy,syr827 @ i2c0 0x40`.
- `rotation = <90>` for correct landscape orientation.
- ADC volume keys, joypad buttons/sticks, RK817 audio + battery calibration
  from stock firmware, UART1 serdev Bluetooth node, speaker-amp GPIO.

### RTL8733BS WiFi
- The board reports SDIO ID `024C:B733` - a Realtek RTL8733BS, despite the
  stock DT claiming `ap6255` (Broadcom). `brcmfmac`, staging `r8723bs`, and
  patched mainline `rtw88` drivers were all tested and rejected.
- The Realtek vendor driver is patched for Linux 6.12 and integrated as a
  ROCKNIX kernel-module package (`scripts/patch_rtl8733bs_612.py`).
- FullMAC SAE never completes association, so the patch drops the
  `NL80211_FEATURE_SAE` flag - iwd falls back to WPA2-PSK and
  WPA3-transition networks connect. Details in [WIFI.md](WIFI.md).

### RTL8733BS Bluetooth
- BT half of the combo chip on UART1 (Realtek H5 three-wire). Mainline
  `btrtl` lacks the 8733BS entry - added by
  `kernel/0102-e5p-btrtl-rtl8733bs.patch`.
- Firmware extracted from the stock vendor partition
  (`firmware/rtl_bt/`).
- Warm reboot with an active H5 session wedges the chip; a clean detach at
  shutdown (`system.d/e5p-bt-detach.service`) prevents it. Details in
  [BLUETOOTH.md](BLUETOOTH.md).

### Device quirks (`quirks/GameMT E5 Plus/`)
- `010-led_control` - LED menu in EmulationStation; hides the brightness
  menu (plain GPIO LEDs, no PWM).
- `050-audio_path` - speakers are wired to the HP path through an external
  amp; RK817's SPKOUT pin is unconnected. Forces Playback Mux = HP and the
  Android-equivalent master volume.
- `bin/ledcontrol`, `bin/bt-detach` - device-specific helpers picked up by
  ROCKNIX's quirk dispatcher.

## Re-applying on a ROCKNIX rebase

This port currently targets **ROCKNIX `20260601`**. Portable artifacts:

1. `kernel/panel-e5p.c` + `kernel/panel-generic-dsi.c`
2. `kernel/0101-*.patch` + `kernel/0102-*.patch` →
   `projects/Rockchip/devices/RK3566/patches/linux/`
3. `dts/rk3566-e5p.dts`
4. `scripts/integrate_postpatch.py`
5. `RTL8733BS` kernel-module package
   (vendor driver + `scripts/patch_rtl8733bs_612.py`)
6. `firmware/rtl_bt/` BT firmware package
7. `quirks/GameMT E5 Plus/` → `packages/hardware/quirks/devices/`
8. `system.d/e5p-bt-detach.service` → quirks package `system.d/` +
   `enable_service` in `post_install`
