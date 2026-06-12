#!/bin/busybox sh
# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2026  Yiğit Budak <https://github.com/yibudak>
#
# Minimal busybox initramfs for early kernel-first-light testing on the E5 Plus.
# Mounts proc/sys/dev, dumps DRM/panel diagnostics to the boot FAT partition,
# and drops to a shell.

/bin/busybox mount -t proc proc /proc 2>/dev/null
/bin/busybox mount -t sysfs sys /sys 2>/dev/null
/bin/busybox mount -t devtmpfs dev /dev 2>/dev/null
# reattach stdio to the console (initramfs stdio safety net)
exec </dev/console >/dev/console 2>&1
/bin/busybox --install -s /bin

# Find the boot FAT (the one holding KERNEL-E5P) and dump diagnostics to it.
mkdir -p /boot
BOOTDEV=""
for d in /dev/mmcblk0p1 /dev/mmcblk1p1 /dev/mmcblk2p1 /dev/mmcblk0p4 /dev/mmcblk1p4 /dev/mmcblk2p4; do
	if mount -t vfat "$d" /boot 2>/dev/null; then
		if [ -f /boot/KERNEL-E5P ]; then BOOTDEV="$d"; break; fi
		umount /boot 2>/dev/null
	fi
done

LOG=/boot/e5p-boot-log.txt
{
	echo "=== E5P BOOT LOG ==="
	echo "bootdev=$BOOTDEV"
	echo "cmdline: $(cat /proc/cmdline)"
	echo ""
	echo "--- fb0 geometry ---"
	for f in virtual_size rotate stride bits_per_pixel name; do
		echo "fb0/$f = $(cat /sys/class/graphics/fb0/$f 2>/dev/null)"
	done
	echo ""
	echo "--- drm connectors / modes ---"
	for s in /sys/class/drm/*/status; do echo "$s = $(cat $s 2>/dev/null)"; done
	for m in /sys/class/drm/*/modes; do echo "$m: $(cat $m 2>/dev/null)"; done
	echo ""
	echo "--- backlight ---"
	for b in /sys/class/backlight/*/; do
		echo "$b brightness=$(cat ${b}brightness 2>/dev/null) actual=$(cat ${b}actual_brightness 2>/dev/null) power=$(cat ${b}bl_power 2>/dev/null) max=$(cat ${b}max_brightness 2>/dev/null)"
	done
	echo ""
	echo "--- dmesg: panel/dsi/drm/vop/backlight ---"
	dmesg | grep -iE "panel|dsi|drm|rockchip|backlight|vop|e5p"
	echo ""
	echo "=== FULL DMESG ==="
	dmesg
} > "$LOG" 2>&1
sync

clear
echo ""
echo "==================================================="
echo "   E5 PLUS - CUSTOM KERNEL BOOT OK"
echo "   log written -> $LOG (dev=$BOOTDEV)"
echo "==================================================="
dmesg | grep -iE "panel|dsi|drm" | tail -12
echo ""
echo ">>> shell ready:"
exec /bin/busybox sh
