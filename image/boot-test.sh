#!/usr/bin/env bash
# Verify the finished DevOS image boots under UEFI and the baked-in core tools are present.
# Boots the image (fresh instance-id) with a check seed that writes a marker and powers off.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
img="$out/devos.qcow2"
[ -f "$img" ] || { echo "ERROR: image not found: $img (run build-cloud-image.sh first)"; exit 1; }

cp image/seed/user-data "$out/verify-user-data"
cp image/seed/meta-data "$out/verify-meta-data"
cloud-localds "$out/verify-seed.iso" "$out/verify-user-data" "$out/verify-meta-data"

if bash image/run-vm.sh "$img" "$out/verify-seed.iso" "DEVOS_BOOT_OK_PROFILE_CORE" 600; then
  echo "BOOT TEST PASSED: image boots under UEFI and core profile tools are present."
else
  echo "BOOT TEST FAILED: marker not seen (see serial log above)."
  exit 1
fi
