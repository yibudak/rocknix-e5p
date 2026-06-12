# Flashing & Booting on the E5 Plus

## ⚠️ Safety Rule: SD-Only

**Never touch the internal eMMC.** Test from SD card. If the card fails to boot, remove it and the device returns to stock Android.

To recover the stock eMMC, restore the full backup image you made before starting.

## Flashing to SD Card (macOS)

1. Insert your microSD card and identify its device (e.g. `/dev/disk4`).
2. Unmount it:
   ```bash
   diskutil unmountDisk /dev/rdiskX
   ```
3. Write the image:
   ```bash
   gunzip -c ROCKNIX-RK3566.aarch64-YYYYMMDD-Generic.img.gz | \
     sudo dd of=/dev/rdiskX bs=1m status=progress
   ```
   Replace `X` with your actual disk number. Use `rdisk` for raw speed.

## Critical: Boot Configuration

The Generic ROCKNIX image uses `FDTDIR /device_trees` in `extlinux.conf`, which lets U-Boot auto-pick a DTB by board name. The E5 Plus is **not** in U-Boot's board list, so you **must** explicitly point to our DTB.

1. Mount the FAT boot partition (partition 1 on the SD card):
   ```bash
   sudo mkdir -p /mnt/sd-boot
   sudo mount -t msdos /dev/diskXs1 /mnt/sd-boot
   ```

2. Edit `extlinux.conf`:
   ```bash
   sudo sed -i 's|FDTDIR /device_trees|FDT /device_trees/rk3566-e5p.dtb|' \
     /mnt/sd-boot/extlinux/extlinux.conf
   ```

3. Verify the DTB is present:
   ```bash
   ls /mnt/sd-boot/device_trees/rk3566-e5p.dtb   # should be ~57 KB
   ```

4. Unmount:
   ```bash
   sudo umount /mnt/sd-boot
   ```

## First-Boot Verification Checklist

After the ROCKNIX splash and EmulationStation UI appear:

1. **Connect to WiFi** - use the on-screen keyboard or plug in a USB keyboard.
2. **Enable SSH** - ROCKNIX default root password is typically empty or `rocknix`.
3. **Verify drivers loaded** over SSH:
   ```bash
   dmesg | grep -i "panel-e5p\|panfrost\|8733bs\|rk817"
   lsmod | grep -E "joypad|rocknix"
   ```
4. Once WiFi + SSH work, kernel iteration becomes fast: you can `scp` a new `KERNEL` file to `/flash/KERNEL` on the running device and reboot (no more SD card shuffling).

## Kernel-Only Iteration (After M2)

For quick kernel testing without rebuilding the full image:

1. Build only the kernel (see [BUILD.md](BUILD.md)).
2. From the host, copy the new kernel to the device:
   ```bash
   scp build/linux-*/arch/arm64/boot/Image root@<e5p-ip>:/flash/KERNEL
   ```
3. Reboot the device from SSH:
   ```bash
   ssh root@<e5p-ip> reboot
   ```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Black screen after splash | Wrong DTB or panel driver missing | Verify `FDT /device_trees/rk3566-e5p.dtb` in `extlinux.conf` |
| No WiFi | RTL8733BS vendor module missing or wrong DTB | Use `rk3566-e5p.dtb`; see [WIFI.md](WIFI.md) |
| No audio | Missing codec / amplifier GPIO | Check `dmesg` for `rk817` and `spk_amp` probe errors |
| Build fails at `[NNN/667]` | OOM or dead source URL | Rebuild with `-j4`, or fix the source URL / checksum |
