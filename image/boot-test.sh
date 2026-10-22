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
# Unique instance-id per boot so cloud-init re-runs runcmd (and re-emits the marker)
# when the same image is booted several times (normal / Secure Boot / TPM).
printf 'instance-id: devos-verify-%s\nlocal-hostname: devos\n' \
  "$(date +%s)-$$-sb${SECBOOT:-0}-tpm${TPM:-0}" > "$out/verify-meta-data"
cloud-localds "$out/verify-seed.iso" "$out/verify-user-data" "$out/verify-meta-data"

marker="${MARKER:-DEVOS_BOOT_OK_PROFILE_CORE}"
if bash image/run-vm.sh "$img" "$out/verify-seed.iso" "$marker" 600; then
  echo "BOOT TEST PASSED (SECBOOT=${SECBOOT:-0} TPM=${TPM:-0}): /$marker/ seen."
else
  echo "BOOT TEST FAILED: /$marker/ not seen (see serial log above)."
  exit 1
fi
