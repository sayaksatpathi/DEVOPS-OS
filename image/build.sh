#!/usr/bin/env bash
# DevOS image builder (SKELETON — not yet functional).
#
# This orchestrates "Path A" from docs/build-and-release.md: customize a pinned Ubuntu
# 26.04.1 Desktop ISO inside a disposable builder VM so the DevOps profiles are baked in.
#
# SAFETY: it refuses to run unless it is on Linux with the required tooling, and it never
# touches the host's disk or bootloader. It is intentionally incomplete — the customization
# steps are marked TODO and must be implemented and proven in a VM before this builds images.
set -euo pipefail

PROFILES="core"
BASE_ISO=""

usage() { echo "usage: sudo $0 --profiles core,containers --base <pinned-ubuntu-26.04.1.iso>"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profiles) PROFILES="$2"; shift 2 ;;
    --base) BASE_ISO="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

# --- Preconditions (fail loudly instead of producing a broken image) ---------------
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "ERROR: image build must run on a Linux builder VM, not $(uname -s)." >&2
  echo "       See docs/build-and-release.md for the required environment." >&2
  exit 1
fi

missing=0
for tool in qemu-system-x86_64 xorriso; do
  command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: required tool not found: $tool" >&2; missing=1; }
done
[[ -n "$BASE_ISO" && -f "$BASE_ISO" ]] || { echo "ERROR: --base <pinned ISO> is required and must exist" >&2; missing=1; }
[[ "$missing" -eq 0 ]] || { echo "Aborting: environment not ready for a build." >&2; exit 1; }

echo "DevOS build (skeleton)"
echo "  profiles : $PROFILES"
echo "  base ISO : $BASE_ISO"
echo
echo "NOT IMPLEMENTED YET. The build pipeline must:"
echo "  1. Verify the base ISO checksum/signature against the pinned manifest."
echo "  2. Unpack the ISO and enter a chroot of the squashfs root."
echo "  3. Run: devos profile apply ${PROFILES//,/ } --confirm   (into the image root)"
echo "  4. Image hygiene: reset machine-id, remove SSH host keys, clear builder creds/logs,"
echo "     install the devos-firstboot unit."
echo "  5. Repack to image/out/devos-<version>.iso and emit .sha256 + SBOM."
echo "  6. Boot-test the result in QEMU/OVMF (never on a real disk)."
exit 3   # 3 = not implemented; honest non-zero exit
