#!/usr/bin/env bash
# Boot a qcow2 image under UEFI (OVMF) in QEMU with a NoCloud seed, capture the serial
# console, and wait for a success marker. Used both to PROVISION the image (first boot
# runs devos apply, where qemu user-mode networking provides working DNS) and to VERIFY
# the finished image boots. Uses KVM if available, else TCG. Exits 0 iff the marker
# appears before the timeout.
#
# usage: run-vm.sh <image.qcow2> <seed.iso> <marker-regex> [timeout-seconds]
set -euo pipefail

img="$1"; seed="$2"; marker="$3"; tmo="${4:-900}"
out="$(cd "$(dirname "$img")" && pwd)"

code="$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd 2>/dev/null | head -1 || true)"
varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd 2>/dev/null | head -1 || true)"
[ -n "$code" ] && [ -n "$varstpl" ] || { echo "ERROR: OVMF firmware not found (install 'ovmf')"; exit 1; }

vars="$out/OVMF_VARS.fd"; cp -f "$varstpl" "$vars"
log="$out/serial.log"; : > "$log"
accel="tcg"; [ -w /dev/kvm ] && accel="kvm:tcg"
echo "booting $(basename "$img") (accel=$accel, timeout=${tmo}s), waiting for /$marker/"

timeout "$tmo" qemu-system-x86_64 \
  -machine q35 -accel "$accel" -cpu max -m 4096 -smp 2 \
  -drive if=pflash,format=raw,readonly=on,file="$code" \
  -drive if=pflash,format=raw,file="$vars" \
  -drive file="$img",if=virtio,format=qcow2 \
  -drive file="$seed",if=virtio,format=raw \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
  -display none -serial file:"$log" &
qp=$!

ok=0
iters=$(( tmo / 5 ))
for _ in $(seq 1 "$iters"); do
  if grep -qE "$marker" "$log" 2>/dev/null; then ok=1; break; fi
  if grep -qE "DEVOS_(PROVISION|BOOT)_FAIL" "$log" 2>/dev/null; then break; fi
  kill -0 "$qp" 2>/dev/null || break
  sleep 5
done
kill "$qp" 2>/dev/null || true
wait "$qp" 2>/dev/null || true

echo "---- serial tail ----"
tail -60 "$log" 2>/dev/null || true
echo "---------------------"
[ "$ok" = 1 ]
