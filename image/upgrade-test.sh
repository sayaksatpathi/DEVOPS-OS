#!/usr/bin/env bash
# OS-upgrade test (gap #4): boot the built image, run `apt full-upgrade` in-guest, reboot,
# and verify the upgraded system boots back to a login prompt. Disposable VM only.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
img="$out/devos.qcow2"
[ -f "$img" ] || { echo "ERROR: image not found: $img"; exit 1; }

cp image/seed/upgrade-user-data "$out/upgrade-user-data"
printf 'instance-id: devos-upgrade-%s\nlocal-hostname: devos\n' "$(date +%s)" > "$out/upgrade-meta-data"
cloud-localds "$out/upgrade-seed.iso" "$out/upgrade-user-data" "$out/upgrade-meta-data"

code="$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd 2>/dev/null | head -1)"
varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd 2>/dev/null | head -1)"
cp -f "$varstpl" "$out/OVMF_VARS.fd"
accel="tcg"; [ -w /dev/kvm ] && accel="kvm"
log="$out/upgrade-serial.log"; : > "$log"

echo "booting image for OS upgrade (accel=$accel)"
timeout 1800 qemu-system-x86_64 \
  -machine q35 -accel "$accel" -cpu max -m 4096 -smp 2 \
  -drive if=pflash,format=raw,readonly=on,file="$code" \
  -drive if=pflash,format=raw,file="$out/OVMF_VARS.fd" \
  -drive file="$img",if=virtio,format=qcow2 \
  -drive file="$out/upgrade-seed.iso",if=virtio,format=raw \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
  -display none -serial file:"$log" &
qp=$!

upgraded=0 rebooted=0
for _ in $(seq 1 180); do
  if [ "$upgraded" = 0 ] && grep -q "DEVOS_UPGRADE_OK" "$log" 2>/dev/null; then
    echo "upgrade applied"; upgraded=1
  fi
  grep -q "DEVOS_UPGRADE_FAIL" "$log" 2>/dev/null && break
  # a login prompt AFTER the upgrade marker means it rebooted and came back up
  if [ "$upgraded" = 1 ] && grep -qE "login:" "$log" 2>/dev/null \
     && [ "$(grep -c 'login:' "$log")" -ge 1 ]; then
    # ensure the login appears after the upgrade marker
    if awk '/DEVOS_UPGRADE_OK/{f=1} f&&/login:/{found=1} END{exit !found}' "$log"; then
      rebooted=1; break
    fi
  fi
  kill -0 "$qp" 2>/dev/null || break
  sleep 10
done
kill "$qp" 2>/dev/null || true; wait "$qp" 2>/dev/null || true

echo "---- upgrade serial tail ----"; tail -30 "$log" 2>/dev/null || true
if [ "$upgraded" = 1 ] && [ "$rebooted" = 1 ]; then
  echo "UPGRADE TEST PASSED: full-upgrade applied and the system rebooted to a login prompt."
else
  echo "UPGRADE TEST FAILED (upgraded=$upgraded rebooted=$rebooted)."
  exit 1
fi
