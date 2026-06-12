# Repository Guidelines

## Project Structure & Module Organization

This is the GameMT E5 Plus ROCKNIX port overlay, not the full ROCKNIX tree.
Kernel-facing sources live in `kernel/` and `dts/`, including panel drivers,
Linux patches, and `rk3566-e5p.dts`. Runtime integration files are in
`quirks/GameMT E5 Plus/`, `system.d/`, and `firmware/rtl_bt/`. Helper scripts
are in `scripts/`. Subsystem docs are in `docs/`, with images under
`docs/images/` and captured register data under `docs/data/`.

## Build, Test, and Development Commands

- `python3 -m py_compile scripts/*.py` - CI's Python syntax check.
- `shellcheck -e SC1091 -S warning scripts/*.sh "quirks/GameMT E5 Plus/010-led_control" "quirks/GameMT E5 Plus/050-audio_path" "quirks/GameMT E5 Plus/bin/"*` - CI's shell lint.
- `docker exec e5p-build bash -lc 'python3 /path/to/rocknix-e5p/scripts/integrate_postpatch.py'` - injects E5P files into the ROCKNIX tree.
- `docker exec e5p-build bash -lc 'cd /root/rocknix && DEVICE_ROOT=RK3566 PROJECT=Rockchip DEVICE=RK3566 ARCH=arm ./scripts/build_distro'` - builds the required 32-bit compat root.
- `docker exec e5p-build bash -lc 'cd /root/rocknix && PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build_distro'` - builds the full image.

After distro builds, confirm success with `grep realexit=` and check that the
package counter advanced past the previous failure point.

## Coding Style & Naming Conventions

Kernel C follows Linux kernel style: tabs, lower-case symbols, and minimal
local abstractions. Shell under `quirks/` and initramfs paths must stay
BusyBox/POSIX-compatible. Python scripts use Python 3, simple top-level
constants, and explicit nonzero returns from `main()`.

## Testing Guidelines

There is no unit-test suite. Run the CI-equivalent lint commands above before
opening a PR. For hardware-facing changes in `kernel/`, `dts/`, `firmware/`,
`quirks/`, or `system.d/`, test on real E5 Plus hardware when possible and
capture useful logs with `journalctl -b` and `dmesg` over SSH.

## Commit & Pull Request Guidelines

Recent history uses short, imperative subjects with optional scopes, such as
`docs: review and slim README and contributor docs`, `CI: scan full history
with gitleaks binary`, and `Fix 0102 btrtl patch context`. Keep PRs focused on
one fix or feature. Include what changed, how it was tested, and whether real
hardware was used. Add screenshots only for visible UI or doc image changes.

## Security & Agent-Specific Instructions

All development should boot from SD card. Do not write to internal eMMC, which
keeps stock Android recoverable. Treat `firmware/rtl_bt/*.bin` as proprietary
Realtek blobs and document source and license implications before replacing
them. Before opening a PR, do not run OCR by default; for large, broad, or
risky changes, ask first.
