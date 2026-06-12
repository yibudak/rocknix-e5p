<div align="center">

<img src="docs/images/banner.jpg" alt="ROCKNIX for GameMT E5 Plus" width="100%">

**ROCKNIX for the GameMT E5 Plus handheld - Linux retro gaming, booted from SD card.**

[![CI](https://github.com/yibudak/rocknix-e5p/actions/workflows/ci.yml/badge.svg)](https://github.com/yibudak/rocknix-e5p/actions/workflows/ci.yml) [![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html) [![Platform](https://img.shields.io/badge/Platform-ROCKNIX-orange.svg)](https://github.com/ROCKNIX/distribution) [![SoC](https://img.shields.io/badge/SoC-RK3566-green.svg)](https://www.rock-chips.com/uploads/pdf/2022.8.26/191/RK3566%20Brief%20Datasheet.pdf)

[🕹️ What Works](#️-what-works) · [📸 Gallery](#-gallery) · [💾 Install](#-install) · [🔨 Build](#-build-it-yourself) · [📚 Docs](#-documentation)

</div>

---

## 🧐 What is this?

The GameMT E5 Plus is a budget retro handheld (Rockchip RK3566, 5" screen)
that ships with Android. This project ports [ROCKNIX](https://github.com/ROCKNIX/distribution),
an open-source Linux gaming distribution, to it: EmulationStation, RetroArch
and dozens of emulators boot from a microSD card.

The internal storage stays untouched. Pull the SD card and the device boots
stock Android again.

It's the first working Linux port for this device. Earlier community attempts
failed on a wrong CPU-regulator definition, which this port fixes alongside a
custom display driver. See [docs/PORTING.md](docs/PORTING.md) for the details.

---

## 🕹️ What Works

Verified on real hardware:

| | Feature | Status | Notes |
|:---:|:---|:---:|:---|
| 📺 | Display (5" 720×1280, 60 Hz) | ✅ Works | Custom panel driver, correct colors & orientation |
| 🎮 | Buttons, D-pad, analog sticks | ✅ Works | Full mapping in EmulationStation & emulators |
| 🔊 | Speakers & headphone jack | ✅ Works | Auto jack detection, volume tuned to stock levels |
| 📶 | WiFi (2.4 + 5 GHz) | ✅ Works | Both bands, including mixed WPA2/WPA3 networks |
| 🎧 | Bluetooth | ✅ Works | Pairing and BLE scan verified |
| 🔋 | Battery % & charging | ✅ Works | Calibration data taken from stock firmware |
| 💡 | LEDs | ✅ Works | On/off control from the settings menu |
| 😴 | Sleep / wake | ✅ Works | Deep suspend |
| ⚡ | CPU boost to 1.99 GHz | ✅ Works | Vendor-binned top speed, toggle in settings |
| 🖥️ | Mini-HDMI output | 🧪 Not tested yet | |
| 🎯 | Emulator deep-testing | 🧪 In progress | PSP, PS1, Dreamcast, N64, SNES, GBA test library |
| 📳 | Rumble | ❌ No hardware | The board has no vibration motor - not a software issue |

---

## 📸 Gallery

<div align="center">
<table>
  <tr>
    <td align="center">
      <img src="docs/images/hero.jpg" width="400" alt="GameMT E5 Plus booting ROCKNIX, joystick LEDs glowing through the transparent shell"><br>
      <sub>Boot splash - joystick LEDs shining through the shell</sub>
    </td>
    <td align="center">
      <img src="docs/images/emulationstation.jpg" width="400" alt="EmulationStation system list running on the E5 Plus"><br>
      <sub>EmulationStation, ready to play</sub>
    </td>
  </tr>
</table>
</div>

---

## 💾 Install

Grab the latest `ROCKNIX-RK3566.aarch64-*-E5_Plus.img.7z` from
[Releases](https://github.com/yibudak/rocknix-e5p/releases). The `E5_Plus`
image is preconfigured for this device, or you can
[build it yourself](#-build-it-yourself).

You need a microSD card (16 GB+, A1-class recommended).

**1. Extract and flash the image** (macOS/Linux):

```bash
7z x ROCKNIX-RK3566.aarch64-*-E5_Plus.img.7z
sudo dd if=ROCKNIX-RK3566.aarch64-*-E5_Plus.img of=/dev/rdiskX bs=1m status=progress
```

**2. Insert the SD card and power on.** ROCKNIX boots into EmulationStation.
Connect to WiFi, enable SSH if you want, drop your ROMs into `/storage/roms`.

Everything runs from the SD card, so you can't brick the device. Remove the
card and stock Android boots again. Full walkthrough and troubleshooting:
[docs/FLASHING.md](docs/FLASHING.md).

> ℹ️ Flashing a **Generic** RK3566 image instead? Edit
> `extlinux/extlinux.conf` on the SD card's FAT partition and replace the
> `FDTDIR` line with `FDT /device_trees/rk3566-e5p.dtb` - the E5 Plus isn't
> in U-Boot's board list. The `E5_Plus` image already has this set.

---

## 🔨 Build It Yourself

The image builds inside ROCKNIX's Docker container:

```bash
# inject the E5P kernel driver + device tree into the ROCKNIX tree
python3 scripts/integrate_postpatch.py

# build the full image (takes a few hours)
PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build_distro
```

Container setup, kernel-only rebuilds and build gotchas are in
[docs/BUILD.md](docs/BUILD.md).

---

## 📚 Documentation

Each subsystem has its own write-up, including how it was debugged. Useful
if you're porting Linux to another RK3566 device.

| Doc | What's inside |
|:---|:---|
| [PORTING.md](docs/PORTING.md) | How the port works, key fixes, rebase checklist |
| [BUILD.md](docs/BUILD.md) | Building the image from source |
| [FLASHING.md](docs/FLASHING.md) | SD-card flashing & first boot |
| [DISPLAY.md](docs/DISPLAY.md) | Panel bring-up & the line-shift/color-rotation hunt |
| [WIFI.md](docs/WIFI.md) | RTL8733BS driver, Linux 6.12 fixes, WPA3 workaround |
| [BLUETOOTH.md](docs/BLUETOOTH.md) | BT bring-up, firmware extraction, reboot-wedge fix |
| [AUDIO.md](docs/AUDIO.md) | Speaker wiring quirk & volume tuning |
| [BATTERY.md](docs/BATTERY.md) | Fuel-gauge calibration from stock firmware |
| [LEDS.md](docs/LEDS.md) | LED control via the ROCKNIX quirk system |
| [VIBRATION.md](docs/VIBRATION.md) | Why there is no rumble (no motor on the board) |

---

## 🤝 Contributing

Testing on real hardware helps most: flash, play, report. Bug reports,
doc fixes and PRs are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📜 License

- `kernel/panel-e5p.c` - **GPL-2.0**
- `dts/rk3566-e5p.dts` - **GPL-2.0+ OR MIT**
- Scripts & docs - **GPL-2.0** or **MIT** where noted

See [LICENSE](LICENSE) for the full text.

> ⚠️ **Firmware notice:** `firmware/rtl_bt/rtl8733bs_fw.bin` and
> `rtl8733bs_config.bin` are proprietary Realtek blobs extracted from the
> stock Android vendor partition. They are not covered by this repository's
> license; copyright belongs to Realtek Semiconductor Corp. They're
> redistributed here to make the device work, like the `linux-firmware` tree.
> Rights holders who object can open an issue.

---

## 🙏 Acknowledgements

- [**ROCKNIX**](https://github.com/ROCKNIX/distribution) team for the immutable gaming distro
- **Powkiddy X55** device tree authors for the RK3566 base
- **Mainline Linux** `panel-himax-hx8394.c` authors for the driver structure

---

<div align="center">

Maintained by [**@yibudak**](https://github.com/yibudak)

⭐ **Running ROCKNIX on your E5 Plus? Star the repo - it helps others find it.** ⭐

</div>

---

## ⚠️ Disclaimer

Unofficial community port, not affiliated with GameMT or ROCKNIX. Use at your
own risk. It stays low-risk because it boots from SD card only and never
writes to the stock eMMC.
