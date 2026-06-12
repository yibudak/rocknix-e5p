# E5P Bluetooth: RTL8733BS UART (H5) bring-up

**Status: WORKING (2026-06-11).** Controller up (`hci0`), BLE scan finds
neighbors, firmware `fw version 0xdda9b625` loads.

## Hardware

RTL8733BS combo chip: WiFi half on SDIO (sdmmc1, out-of-tree `8733bs` driver),
BT half on **UART1** (m0 pins, RTS/CTS flow control) speaking Realtek H5
(three-wire). From the stock Android DT (`bluetooth-platdata`):

| Signal | GPIO |
|---|---|
| BT enable/reset | GPIO0_C1 (active high) |
| device wake | GPIO0_B6 |
| host wake | GPIO0_B5 |
| UART RTS | GPIO2_B5 (uart1 m0) |
| 32k clock | rk817 clkout2 (already running via sdio_pwrseq ext_clock) |

Chip identifies as `hci_ver=08 hci_rev=000f lmp_ver=08 lmp_subver=8723` -
the 8723F family. USB sibling (8733BU) is in mainline btrtl; the UART/SDIO
**BS variant is not** → kernel patch needed.

## Firmware

NOT in upstream linux-firmware. Extracted from stock Android vendor partition:
`super.img` → LP metadata parse (vendor at 0x4cd00000) → debugfs →
`/vendor/etc/firmware/rtl8733bs_8723fs_fw` + `rtl8733bs_8723fs_config`.
Renamed to what the btrtl patch expects:

- `firmware/rtl_bt/rtl8733bs_fw.bin` (46156 bytes, "Realtech" magic)
- `firmware/rtl_bt/rtl8733bs_config.bin` (33 bytes, magic 55ab2387; contains
  UART baud 0x04928002 = 1.5M - btrtl parses this for the H5 link)

There is also a `_config_vendor` variant (37 bytes, one extra reg write at
0x00d8); the plain config works.

## Kernel changes

1. `kernel/0102-e5p-btrtl-rtl8733bs.patch` - adds the 8733BS table entry to
   `drivers/bluetooth/btrtl.c`:
   `IC_INFO(RTL_ROM_LMP_8723B, 0xf, 0x8, HCI_UART)` →
   `rtl_bt/rtl8733bs_fw` + `rtl_bt/rtl8733bs_config`. (Project id 19 = 8733B
   was already in the mainline fw-parser table.)
2. dts: `&uart1` enabled (m0 xfer/cts/rts, `uart-has-rtscts`) with serdev
   `bluetooth` child node, compatible **`realtek,rtl8723ds-bt`** (reuses the
   generic Realtek H5 data in `hci_h5.c`; no new compatible needed).

## Two hardware traps worth knowing

- `hci_h5.c` sets `HCI_UART_INIT_PENDING`: for serdev H5, **hci0 only
  registers after the controller answers the H5 SYNC**. No answer → no hci0,
  no error anywhere - pure silence (`/sys/class/bluetooth` empty, driver
  bound, TX `seq 0 ... type 15` frames visible with dyndbg, zero RX).
- **Warm-reboot wedge**: rebooting while an H5 session is ACTIVE (hci0 up)
  wedges the chip - VBAT survives a warm `reboot`, the chip keeps its session
  state and then ignores H5 SYNC entirely. Nothing revives it within a boot
  (rmmod/insmod, unbind/bind, enable-GPIO low for 15s, attaching at 1.5M
  instead of 115200, early vs late attach - all tested, all dead). Only a
  TRUE poweroff resets it. BUT: a **clean detach before reboot**
  (`rmmod hci_uart` → `h5_btrtl_close` → enable GPIO low) leaves the chip
  recoverable - next boot's attach works.

## Image integration

- `kernel/0102-e5p-btrtl-rtl8733bs.patch` → copy into ROCKNIX
  `projects/Rockchip/devices/RK3566/patches/linux/`; it then applies
  automatically at kernel build.
- `dts/rk3566-e5p.dts` → enables `&uart1` + serdev bluetooth node; the
  patched btrtl autoloads via serdev and works on first attach.
- Firmware blobs `firmware/rtl_bt/rtl8733bs_{fw,config}.bin` → packaged into
  the image firmware dir (`rtl_bt/`); model the package on
  `packages/linux-firmware/rtl8723bs_bt` or a local-`sources/` package
  (blobs in-tree, `makeinstall_target` copies to
  `$(get_full_firmware_dir)/rtl_bt/`).
- Warm-reboot wedge handled by `system.d/e5p-bt-detach.service` +
  `quirks/GameMT E5 Plus/bin/bt-detach`: a oneshot unit whose ExecStop runs
  in the shutdown transaction and detaches the H5 link cleanly (same pattern
  as ROCKNIX's `led-poweroff.service`). Enable it from the quirks package
  (`enable_service e5p-bt-detach.service` in `post_install`).

## Debugging notes

- `bluetoothctl scan on` exits instantly when stdout is not a tty - scans ran
  for milliseconds and "found nothing". Use `bluetoothctl --timeout 15 scan on`.
- dyndbg to watch the H5 link: `echo "file hci_h5.c +p" >
  /sys/kernel/debug/dynamic_debug/control` - TX-with-no-RX means the chip is
  not answering; `(null)` device name in those logs is normal pre-registration.
- rtk_hciattach (Caesar-github/rkwifibt, used by JELOS-era images on
  /dev/ttyS1) is the userspace fallback if serdev ever misbehaves.
