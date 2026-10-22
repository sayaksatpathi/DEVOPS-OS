#!/usr/bin/env bash
# Boot the DevOS installer ISO in QEMU (UEFI) with a blank target disk and let the
# unattended autoinstall run. Passes when the install writes DEVOS_INSTALL_OK to the
# serial console (installed Ubuntu + baked-in profile tools verified), before timeout.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
iso="$out/devos-installer-amd64.iso"
[ -f "$iso" ] || { echo "ERROR: installer ISO not found: $iso"; exit 1; }

code="$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd 2>/dev/null | head -1 || true)"
varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd 2>/dev/null | head -1 || true)"
[ -n "$code" ] && [ -n "$varstpl" ] || { echo "ERROR: OVMF not found"; exit 1; }
cp -f "$varstpl" "$out/OVMF_VARS.fd"

# blank target disk the installer writes to (disposable)
qemu-img create -f qcow2 "$out/target.qcow2" 16G >/dev/null

accel="tcg"; [ -w /dev/kvm ] && accel="kvm"
log="$out/installer-serial.log"; : > "$log"
tmo=3000
echo "booting installer ISO (accel=$accel, timeout=${tmo}s), waiting for DEVOS_INSTALL_OK"
timeout "$tmo" qemu-system-x86_64 \
  -machine q35 -accel "$accel" -cpu max -m 4096 -smp 2 \
  -drive if=pflash,format=raw,readonly=on,file="$code" \
  -drive if=pflash,format=raw,file="$out/OVMF_VARS.fd" \
  -drive file="$out/target.qcow2",if=virtio,format=qcow2 \
  -drive file="$iso",if=virtio,media=cdrom \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
  -boot d -display none -serial file:"$log" &
qp=$!

ok=0
for _ in $(seq 1 $((tmo/10))); do
  if grep -q "DEVOS_INSTALL_OK" "$log" 2>/dev/null; then ok=1; break; fi
  if grep -q "DEVOS_INSTALL_FAIL" "$log" 2>/dev/null; then break; fi
  kill -0 "$qp" 2>/dev/null || break
  sleep 10
done
kill "$qp" 2>/dev/null || true
wait "$qp" 2>/dev/null || true

echo "---- installer serial tail ----"; tail -60 "$log" 2>/dev/null || true
echo "-------------------------------"
if [ "$ok" = 1 ]; then
  echo "INSTALLER TEST PASSED: unattended install completed and DevOS tools are present."
else
  echo "INSTALLER TEST FAILED: DEVOS_INSTALL_OK not seen (see serial tail)."
  exit 1
fi
