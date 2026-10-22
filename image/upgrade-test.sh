#!/usr/bin/env bash
# OS-upgrade test (gap #4): boot the built image, apply `apt full-upgrade` in-guest, and
# confirm the upgrade completes. Uses the proven run-vm.sh helper (reliable boot + serial).
# Hard pass = the upgrade applied cleanly in-guest (DEVOS_UPGRADE_OK). Disposable VM only.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
img="$out/devos.qcow2"
[ -f "$img" ] || { echo "ERROR: image not found: $img"; exit 1; }

# Build the upgrade seed (unique instance-id so cloud-init runs runcmd).
cp image/seed/upgrade-user-data "$out/upgrade-user-data"
printf 'instance-id: devos-upgrade-%s\nlocal-hostname: devos\n' "$(date +%s)" > "$out/upgrade-meta-data"
cloud-localds "$out/upgrade-seed.iso" "$out/upgrade-user-data" "$out/upgrade-meta-data"

# run-vm.sh boots under UEFI, captures serial to image/out/serial.log, waits for the marker.
if bash image/run-vm.sh "$img" "$out/upgrade-seed.iso" "DEVOS_UPGRADE_OK" 1800; then
  cp -f "$out/serial.log" "$out/upgrade-serial.log" 2>/dev/null || true
  echo "UPGRADE TEST PASSED: apt full-upgrade applied cleanly in-guest."
else
  cp -f "$out/serial.log" "$out/upgrade-serial.log" 2>/dev/null || true
  echo "UPGRADE TEST FAILED: DEVOS_UPGRADE_OK not seen (see serial)."
  exit 1
fi
