#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2026  Yiğit Budak <https://github.com/yibudak>
"""
Inject E5P panel driver + device tree into ROCKNIX's kernel package.mk post_patch.

This script modifies packages/kernel/linux/package.mk inside the ROCKNIX build
tree to copy panel-e5p.c and rk3566-e5p.dts into the kernel source and append
them to the relevant Makefiles. It mirrors how ROCKNIX already injects
panel-generic-dsi.c for RK3566.

Usage (inside the ROCKNIX Docker container):
    python3 /path/to/rocknix-e5p/scripts/integrate_postpatch.py

The script is idempotent: running it twice has no effect.
"""

import sys

PKG_MK = "/root/rocknix/packages/kernel/linux/package.mk"

ANCHOR = 'echo "obj-y" += panel-generic-dsi.o >> ${PKG_BUILD}/drivers/gpu/drm/panel/Makefile'

ADDITION = r'''
    # E5P: custom panel driver + device tree (GameMT E5 Plus)
    cp -v ${ROOT}/projects/Rockchip/devices/${DEVICE}/linux/panel-e5p.c ${PKG_BUILD}/drivers/gpu/drm/panel/
    echo "obj-y += panel-e5p.o" >> ${PKG_BUILD}/drivers/gpu/drm/panel/Makefile
    cp -v ${ROOT}/projects/Rockchip/devices/${DEVICE}/linux/rk3566-e5p.dts ${PKG_BUILD}/arch/arm64/boot/dts/rockchip/
    echo 'dtb-$(CONFIG_ARCH_ROCKCHIP) += rk3566-e5p.dtb' >> ${PKG_BUILD}/arch/arm64/boot/dts/rockchip/Makefile'''


def main() -> int:
    try:
        with open(PKG_MK, "r") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"ERROR: {PKG_MK} not found")
        return 1

    if "panel-e5p.c" in text:
        print("E5P integration already present - nothing to do.")
        return 0

    if ANCHOR not in text:
        print("ERROR: anchor string not found in package.mk")
        return 1

    text = text.replace(ANCHOR, ANCHOR + "\n" + ADDITION, 1)

    with open(PKG_MK, "w") as f:
        f.write(text)

    print("Successfully patched post_patch in package.mk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
