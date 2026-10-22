#!/usr/bin/env bash
# Boot-test the built DevOS cloud image in QEMU under UEFI (OVMF). A NoCloud seed runs
# a check on first boot and writes a marker to the serial console, then powers off.
# Passes iff the marker appears within the timeout. Uses KVM if available, else TCG.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
img="$out/devos.qcow2"
[ -f "$img" ] || { echo "ERROR: image not found: $img (run build-cloud-image.sh first)"; exit 1; }

echo "== build NoCloud seed =="
cloud-localds "$out/seed.iso" image/seed/user-data image/seed/meta-data

code="$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd 2>/dev/null | head -1 || true)"
varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd 2>/dev/null | head -1 || true)"
[ -n "$code" ] && [ -n "$varstpl" ] || { echo "ERROR: OVMF firmware not found (install 'ovmf')"; exit 1; }
cp "$varstpl" "$out/OVMF_VARS.fd"

accel="tcg"
[ -w /dev/kvm ] && accel="kvm:tcg"
echo "== boot image under UEFI (accel=$accel) =="
: > "$out/serial.log"
timeout 480 qemu-system-x86_64 \
  -machine q35 -accel "$accel" -cpu max -m 2048 -smp 2 \
  -drive if=pflash,format=raw,readonly=on,file="$code" \
  -drive if=pflash,format=raw,file="$out/OVMF_VARS.fd" \
  -drive file="$img",if=virtio,format=qcow2 \
  -drive file="$out/seed.iso",if=virtio,format=raw \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
  -display none -serial file:"$out/serial.log" &
qpid=$!

ok=0
for _ in $(seq 1 90); do
  if grep -q "DEVOS_BOOT_OK_PROFILE_CORE" "$out/serial.log" 2>/dev/null; then ok=1; break; fi
  if grep -q "DEVOS_BOOT_FAIL" "$out/serial.log" 2>/dev/null; then break; fi
  kill -0 "$qpid" 2>/dev/null || break
  sleep 5
done
kill "$qpid" 2>/dev/null || true
wait "$qpid" 2>/dev/null || true

echo "---- serial tail ----"
tail -40 "$out/serial.log" 2>/dev/null || true
echo "---------------------"
if [ "$ok" = 1 ]; then
  echo "BOOT TEST PASSED: image boots under UEFI and core profile tools are present."
else
  echo "BOOT TEST FAILED: marker not seen (see serial log above)."
  exit 1
fi
