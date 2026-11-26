#!/usr/bin/env bash
# Installs the studio tech stack in a fresh Linux cloud container (Ubuntu 24.04, Python 3.13).
# Free: no paid service is touched. Run from the repo root:  bash studio/setup/install_cloud.sh
# Then check:  bash studio/setup/check_stack.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== system packages: ffmpeg, sox, Mesa EGL (lets EEVEE render on the CPU with no GPU)"
apt-get update -q
apt-get install -y -q ffmpeg sox unzip libegl1 libegl-mesa0 libgl1-mesa-dri libgles2

echo "== Python packages (Blender 5.2 as a Python module, sound, edit lists)"
pip install --break-system-packages -q -r "$HERE/requirements.txt"

echo "== Rhubarb Lip Sync 1.14.0 (mouth shapes from recorded lines)"
if ! command -v rhubarb >/dev/null; then
  tmp="$(mktemp -d)"
  curl -sSL -o "$tmp/rhubarb.zip" https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip
  unzip -q -o "$tmp/rhubarb.zip" -d /opt/
  ln -sf /opt/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb /usr/local/bin/rhubarb
fi

echo "== done. EEVEE renders need:  export EGL_PLATFORM=surfaceless"
