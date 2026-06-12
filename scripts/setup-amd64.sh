#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2026  Yiğit Budak <https://github.com/yibudak>
#
# Enable amd64 multiarch on an arm64 Ubuntu 24.04 container so ROCKNIX can run
# the prebuilt x86_64 rkbin tools via qemu-x86_64.
set -e
export DEBIAN_FRONTEND=noninteractive

SRC=/etc/apt/sources.list.d/ubuntu.sources
if [ -f "$SRC" ] && ! grep -q "Architectures:" "$SRC"; then
  # pin existing (ports.ubuntu.com) stanzas to arm64
  sed -i '/^Types:/a Architectures: arm64' "$SRC"
fi

# add an amd64-only source pointing at archive.ubuntu.com (which hosts amd64)
cat > /etc/apt/sources.list.d/amd64.sources <<'EOF'
Types: deb
URIs: http://archive.ubuntu.com/ubuntu
Suites: noble noble-updates noble-security
Components: main restricted universe multiverse
Architectures: amd64
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

apt-get update -qq 2>&1 | tail -2
echo "=== install ==="
apt-get install -y -qq \
  libc6:amd64 qemu-user-static \
  xfonts-utils default-jre-headless libwayland-dev wayland-protocols \
  python-is-python3 xsltproc libgl1-mesa-dev libxext-dev golang-go \
  sudo >/dev/null 2>&1
echo "install exit=$?"
echo "=== verify ==="
ls -la /lib64/ld-linux-x86-64.so.2 2>&1 || echo "ld-linux-x86-64 NOT FOUND"
ls -la /lib/x86_64-linux-gnu/libc.so.6 2>&1 || echo "libc.so.6 NOT FOUND"
echo "binfmt qemu-x86_64:"; head -2 /proc/sys/fs/binfmt_misc/qemu-x86_64 2>/dev/null || echo "NOT REGISTERED"
