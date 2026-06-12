<div align="center">

# 🎮 ROCKNIX for GameMT E5 Plus

**An open-source Linux gaming distro port for the GameMT E5 Plus handheld**

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![GitHub stars](https://img.shields.io/github/stars/yibudak/rocknix-e5p?style=social)](https://github.com/yibudak/rocknix-e5p/stargazers)
[![Platform](https://img.shields.io/badge/Platform-ROCKNIX-orange.svg)](https://github.com/ROCKNIX/distribution)
[![SoC](https://img.shields.io/badge/SoC-RK3566-green.svg)](https://www.rock-chips.com/uploads/pdf/2022.8.26/191/RK3566%20Brief%20Datasheet.pdf)

[🚀 Quick Start](#flashing--booting) · [🔧 Build](#building) · [📋 Changelog](#milestones)

</div>

---

> ⚠️ **Work in Progress**
> 
> This port is functional and boots to EmulationStation, but not all hardware features are fully verified yet. See [Milestones](#milestones) for current status.

---

## 📖 Table of Contents

- [📖 Table of Contents](#-table-of-contents)
- [✨ Features](#-features)
- [📱 Device Overview](#-device-overview)
- [🎯 Why This Port Exists](#-why-this-port-exists)
- [📁 Repository Layout](#-repository-layout)
- [🔑 Key Fixes](#-key-fixes)
- [🗺️ Milestones](#️-milestones)
- [🔨 Building](#-building)
- [📡 WiFi](#-wifi)
- [🔋 Battery](#-battery)
- [💾 Flashing & Booting](#-flashing--booting)
- [⬆️ Upstream](#️-upstream)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🙏 Acknowledgements](#-acknowledgements)
- [👤 Author](#-author)
- [⚠️ Disclaimer](#️-disclaimer)

---

## ✨ Features

<div align="center">

| 🖥️ Display | 🎵 Audio | 🌐 Networking | 🎮 Controls |
|:---:|:---:|:---:|:---:|
| Custom MIPI-DSI driver<br>720×1280 @ 60 Hz | RK817 codec<br>Speaker + headphone | RTL8733BS WiFi + Bluetooth<br>both verified on hardware | Full joypad + analog sticks<br>ADC volume keys |

</div>

---

## 📱 Device Overview

<div align="center">

| Feature | Specification |
|:--------|:------------|
| **SoC** | Rockchip RK3566 (4× Cortex-A55 @ 1.8 GHz) |
| **GPU** | Mali-G52 (Panfrost open-source driver) |
| **RAM** | 2 GB LPDDR4 |
| **Storage** | 16 GB eMMC + microSD slot |
| **Display** | 5.0" 720×1280 MIPI-DSI LCD |
| **Audio** | RK817 codec + class-D speaker amp |
| **WiFi / BT** | Realtek RTL8733BS combo (WiFi on SDIO `024C:B733`, BT on UART H5) — both working |
| **Battery** | RK817 fuel gauge; stock-calibrated 4605 mAh design / 5500 mAh qmax |

</div>

> 📝 **Not an Anbernic!** The E5 Plus is a distinct handheld that happens to share the RK3566 SoC with the Powkiddy X55. However, it uses a **different panel**, a **different CPU regulator**, and **different volume key wiring**.

---

## 🎯 Why This Port Exists

Previous community efforts to run Linux on the E5 Plus (e.g. JELOS mods) failed because of an **incorrect regulator node** in the device tree. 

| ❌ Wrong (X55) | ✅ Correct (E5 Plus) |
|:--|:--|
| `tcs4525 @ 0x1c` | `silergy,syr827 @ 0x40` |

This project provides:
- ✅ A corrected mainline kernel
- ✅ A custom DRM panel driver (`panel-e5p.c`)
- ✅ A verified device tree (`rk3566-e5p.dts`)
- ✅ A full ROCKNIX image that boots from **SD card**

---

## 📁 Repository Layout

```
rocknix-e5p/
├── 🎨 kernel/
│   ├── panel-e5p.c                          # Mainline DRM panel driver
│   ├── panel-generic-dsi.c                  # Gated post-init resend (replaces ROCKNIX copy)
│   ├── 0101-e5p-display-android-parity.patch # dw-mipi-dsi Android-parity fixes
│   └── 0102-e5p-btrtl-rtl8733bs.patch       # btrtl 8733BS table entry
├── 🌳 dts/
│   └── rk3566-e5p.dts           # Device tree (corrected regulator, panel, BT, battery)
├── 📦 firmware/
│   └── rtl_bt/                  # RTL8733BS BT firmware (extracted from stock vendor image)
├── ⚙️ quirks/
│   └── GameMT E5 Plus/          # ROCKNIX device quirks (LEDs, audio defaults, BT detach)
├── 🔌 system.d/
│   └── e5p-bt-detach.service    # Clean H5 detach at shutdown (warm-reboot wedge fix)
├── 🔧 scripts/
│   ├── integrate_postpatch.py   # Injects E5P files into ROCKNIX build
│   ├── patch_rtl8733bs_612.py   # RTL8733BS vendor driver fixes (Linux 6.12 + SAE)
│   ├── convert_init_to_generic_dsi.py # Stock DSI init seq converter
│   ├── setup-amd64.sh           # Container multiarch setup
│   └── initramfs-init.sh        # Minimal initramfs for kernel testing
├── 📚 docs/                     # BUILD, FLASHING, WIFI, BLUETOOTH, AUDIO,
│   └── ...                      # DISPLAY, BATTERY, LEDS, VIBRATION + reg dumps
├── README.md
└── LICENSE
```

---

## 🔑 Key Fixes

### 🖥️ `panel-e5p.c`
- Replays the exact **112-command DCS initialization sequence** captured from stock Android
- Compatible string: `gamemt,e5p-panel`
- Based on mainline `panel-himax-hx8394.c`

### 🌳 `rk3566-e5p.dts`
- 🩹 **Critical fix:** `vdd_cpu` corrected to `silergy,syr827 @ i2c0 0x40`
- 🔄 `rotation = <90>` for correct landscape orientation
- 🔊 ADC volume-up / volume-down keys added
- 🔌 Reuses proven RK3566 platform nodes from `rk3566-powkiddy-x55.dts`

### 📡 RTL8733BS WiFi
- The tested board reports SDIO ID `024C:B733`, not a Broadcom/AP6255 module.
- `brcmfmac`, staging `r8723bs`, and patched mainline `rtw88_8723cs` / `rtw88_8723ds` were tested and rejected.
- A Realtek RTL8733BS vendor module (`8733bs.ko`) was patched for Linux 6.12.17 and verified on hardware.
- The driver is integrated as the `RTL8733BS` ROCKNIX kernel-module package, including a fix that disables broken FullMAC SAE so WPA3-transition APs connect via WPA2-PSK.
- WiFi configuration uses ROCKNIX's normal network manager UI; no device-specific helper services.
- See [docs/WIFI.md](docs/WIFI.md) for build notes and low-level live-test commands.

### 🎧 RTL8733BS Bluetooth
- BT half of the combo chip on UART1 (Realtek H5 three-wire); mainline `btrtl` lacks the 8733BS table entry — added by `kernel/0102-e5p-btrtl-rtl8733bs.patch`.
- Firmware extracted from the stock vendor image, shipped under `firmware/rtl_bt/`.
- Warm-reboot wedge fixed by a clean H5 detach at shutdown (`system.d/e5p-bt-detach.service`).
- See [docs/BLUETOOTH.md](docs/BLUETOOTH.md).

### 🔋 RK817 Battery Calibration
- Battery percentage and charge status are exposed by the mainline RK817 charger / fuel gauge driver.
- The DTS now uses stock Android calibration data instead of a guessed 4000 mAh profile.
- Stock calibration reports `design_capacity = 4605 mAh`, `design_qmax = 5500 mAh`, and `bat_res = 67 mOhm`.
- Some retail listings mention 5000 mAh or 6000 mAh packs; those are documented as unverified marketing values, not kernel calibration data.
- See [docs/BATTERY.md](docs/BATTERY.md) for the converted OCV table and runtime verification commands.

---

## 🗺️ Milestones

<div align="center">

| Milestone | Status | Description |
|:----------|:------:|:------------|
| **M1** — Kernel Boots | ✅ | Custom kernel boots, panel lights up |
| **M2** — ROCKNIX Builds | ✅ | Full image compiles and boots to EmulationStation |
| **M3** — Hardware Verify | ✅ | Display, WiFi, Bluetooth, audio, joypad, battery, LEDs all verified on hardware |
| **M4** — Polish | 🔄 | Emulator testing in progress; final image build pending |

</div>

<div align="center">

![Progress](https://progress-bar.xyz/90/?title=Overall+Progress&width=500&color=00aa00)

</div>

---

## 🔨 Building

See [**docs/BUILD.md**](docs/BUILD.md) for the complete guide on building inside the ROCKNIX Docker container.

```bash
# Quick start — full aarch64 distro build
docker exec e5p-build bash -lc \
  'cd /root/rocknix && PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build_distro'
```

## 📡 WiFi

WiFi is verified with the RTL8733BS SDIO vendor driver. The driver is integrated
as a ROCKNIX kernel-module package; ROCKNIX's ConnMan-based WiFi manager owns
association, DHCP/static IP, and DNS.

For the bring-up record and reproduction steps, see [**docs/WIFI.md**](docs/WIFI.md).

## 🔋 Battery

Battery percentage and charge status are handled by the RK817 power-supply
driver. The kernel DTS uses stock firmware calibration data: 4605 mAh design
capacity, 5500 mAh qmax reference, 67 mOhm pack resistance, and the stock OCV
curve.

Retail sources list both 5000 mAh and 6000 mAh capacities for this device, but
those values are not used for kernel calibration until verified by discharge
testing. See [**docs/BATTERY.md**](docs/BATTERY.md).

---

## 💾 Flashing & Booting

See [**docs/FLASHING.md**](docs/FLASHING.md) for detailed SD-card flashing instructions.

> ⚡ **Critical:** The Generic image uses `FDTDIR /device_trees` which auto-picks a DTB. The E5 Plus is **not** in U-Boot's board list, so you **must** change `extlinux.conf` to:
> ```
> FDT /device_trees/rk3566-e5p.dtb
> ```

---

## ⬆️ Upstream

This port currently targets **ROCKNIX `20260601`**. The portable artifacts to re-apply on a future rebase are:

1. `kernel/panel-e5p.c` + `kernel/panel-generic-dsi.c`
2. `kernel/0101-e5p-display-android-parity.patch` + `kernel/0102-e5p-btrtl-rtl8733bs.patch` → `projects/Rockchip/devices/RK3566/patches/linux/`
3. `dts/rk3566-e5p.dts`
4. `scripts/integrate_postpatch.py`
5. `RTL8733BS` kernel-module package (vendor driver + `scripts/patch_rtl8733bs_612.py`)
6. `firmware/rtl_bt/` BT firmware package
7. `quirks/GameMT E5 Plus/` → `packages/hardware/quirks/devices/`
8. `system.d/e5p-bt-detach.service` → quirks package `system.d/` + `enable_service` in `post_install`

---

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug reports
- 💡 Feature suggestions  
- 🔧 Pull requests
- 📖 Documentation improvements

Feel free to [open an issue](https://github.com/yibudak/rocknix-e5p/issues) or submit a PR.

---

## 📜 License

- `kernel/panel-e5p.c` — **GPL-2.0**
- `dts/rk3566-e5p.dts` — **GPL-2.0+ OR MIT**
- Scripts & docs — **GPL-2.0** or **MIT** where noted

See [LICENSE](LICENSE) for the full text.

> ⚠️ **Firmware notice:** `firmware/rtl_bt/rtl8733bs_fw.bin` and
> `rtl8733bs_config.bin` are proprietary Realtek firmware blobs, extracted
> from the device's stock Android vendor partition. They are **not** covered
> by this repository's license; copyright belongs to Realtek Semiconductor
> Corp. They are redistributed here solely to make the device functional, in
> the same spirit as the `linux-firmware` tree. If you are a rights holder
> and object to this distribution, please open an issue.

---

## 🙏 Acknowledgements

- [**ROCKNIX**](https://github.com/ROCKNIX/distribution) team for the excellent immutable gaming distro
- **Powkiddy X55** device tree authors for the RK3566 base
- **Mainline Linux** `panel-himax-hx8394.c` authors for the driver structure

---

## 👤 Author

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/yibudak">
        <img src="https://github.com/yibudak.png?size=100" width="100px;" alt="Yiğit Budak"/><br />
        <sub><b>Yiğit Budak</b></sub>
      </a><br />
      <a href="https://github.com/yibudak">@yibudak</a>
    </td>
  </tr>
</table>

---

<div align="center">

⭐ **Star this repo if you find it useful!** ⭐

</div>

---

## ⚠️ Disclaimer

This is an **unofficial community port**. Use at your own risk. Always back up your data. We strongly recommend keeping the stock eMMC untouched and booting from **SD card only**.
