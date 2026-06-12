# Building ROCKNIX for the E5 Plus

All builds run **inside the Docker container `e5p-build`** (arm64 native, Ubuntu 24.04 base). The ROCKNIX source tree inside the container is at `/root/rocknix`.

## Prerequisites (host — macOS with Apple Silicon)

- Docker Desktop configured for **12 CPU / 12 GB RAM** (minimum).
- Container `e5p-build` created from the ROCKNIX `Dockerfile`.
- After every Docker Desktop restart, re-enable x86_64 emulation:
  ```bash
  docker start e5p-build
  docker run --privileged --rm tonistiigi/binfmt --install amd64
  ```

## Quick Build

### 1. Inject E5P files into the ROCKNIX kernel package

Before building, run the integration script so ROCKNIX knows about our panel driver and device tree (copy or mount this repo into the container first):

```bash
docker exec e5p-build bash -lc \
  'python3 /path/to/rocknix-e5p/scripts/integrate_postpatch.py'
```

Or copy the files into the ROCKNIX tree manually (see `scripts/integrate_postpatch.py` for the exact steps).

### 2. Build the 32-bit ARM compat root (required for box86/box64/wine32)

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && DEVICE_ROOT=RK3566 PROJECT=Rockchip DEVICE=RK3566 ARCH=arm ./scripts/build_distro'
```

`ENABLE_32BIT` defaults to true; the aarch64 `install box86` step copies artifacts from the separate `build.ROCKNIX-RK3566.arm` root. Build this root before (or alongside) the main aarch64 build.

### 3. Build the full aarch64 distro image

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build_distro'
```

This produces ~666 packages and ends with `make image`, generating `.img.gz` files in `/root/rocknix/release/`.

### 4. Copy the image out of the container

```bash
docker cp e5p-build:/root/rocknix/release/ROCKNIX-RK3566.aarch64-$(date +%Y%m%d)-Generic.img.gz ./
```

## Rebuild Only the Kernel

After changing `panel-e5p.c` or `rk3566-e5p.dts`:

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && rm -rf build.ROCKNIX-RK3566.aarch64/.stamps/linux build.ROCKNIX-RK3566.aarch64/linux-* && \
   PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build linux'
```

Then rebuild the image:

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && rm -rf build.ROCKNIX-RK3566.aarch64/.stamps/image build.ROCKNIX-RK3566.aarch64/image && \
   PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build_distro'
```

## Rebuild the RTL8733BS WiFi Module

The E5 Plus test unit reports SDIO ID `024C:B733` and needs the out-of-tree
Realtek RTL8733BS vendor driver. It is integrated as a ROCKNIX kernel-module
package:

```bash
docker exec e5p-build bash -lc \
  'cd /root/rocknix && PROJECT=Rockchip DEVICE=RK3566 ARCH=aarch64 ./scripts/build RTL8733BS'
```

See [WIFI.md](WIFI.md) for the verified source, Linux 6.12 patch script, and
low-level live-test steps.

## Build Gotchas (Already Fixed in Current Container)

1. **rsync 3.3.0 buffer overflow** — ROCKNIX's bundled `toolchain/bin/rsync` crashes on glibc 2.39. Fix: `cp -f /usr/bin/rsync <toolchain>/bin/rsync`. Apply to **both** `.aarch64` and `.arm` build roots if they ever rebuild.
2. **Dead source mirrors** — packages like `keyutils` and `rtmpdump` have dead upstream URLs. Fix: download real tarballs into `sources/<pkg>/`, create `.url` + `.sha256` stamp files, and pin `PKG_SHA256` in `package.mk`.
3. **Git orphaned commits** — upstream may force-push away pinned commits. Fix: pick the nearest surviving commit by date to the release tag.
4. **emulationstation CMake working directory** — `checkgamesdb` target runs a Python script with no `WORKING_DIRECTORY`. Fix: `packages/ui/emulationstation/patches/0001-checkgamesdb-working-dir.patch`.
5. **OOM during parallel linking** — `mame-lr` can exhaust 12 GB RAM with 12 jobs. Fix: rebuild individually with `MAKEFLAGS="-j4"`.
6. **Missing curl** — install `curl` in the container (wine's install step needs it).
7. **DuckStation AppImage 404** — pin a surviving numbered release and update asset name.
8. **portmaster compat.zip drift** — upstream renamed `compat.zip` → `compat.tar.gz`. Fix: update URL and switch `unzip` to `tar` in `package.mk`.

**Always verify real build success with `grep realexit=` in the build output.** The bash `-lc` wrapper can exit 0 even on failures. Also confirm the `[NNN/667]` counter advanced past any prior failure point.
