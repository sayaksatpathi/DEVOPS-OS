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
# FDE (encrypted LVM) needs more headroom; non-FDE is fine at 16G.
tgt_size=16G; [ "${FDE:-0}" = "1" ] && tgt_size=24G
qemu-img create -f qcow2 "$out/target.qcow2" "$tgt_size" >/dev/null

accel="tcg"; [ -w /dev/kvm ] && accel="kvm"
log="$out/installer-serial.log"; : > "$log"
# Encrypted LVM install is heavier, but keep the install phase within the job's 110-min cap
# so the serial log is always uploaded (cancellation skips the upload step).
tmo=3000; [ "${FDE:-0}" = "1" ] && tmo=4200
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
if [ "$ok" != 1 ]; then
  echo "INSTALLER TEST FAILED: DEVOS_INSTALL_OK not seen (see serial tail)."
  exit 1
fi
echo "INSTALLER TEST PASSED: unattended install completed and DevOS tools are present."

echo "== second boot: verify the INSTALLED system boots to a login prompt =="
# Reuse the same OVMF_VARS (it holds the boot entry the installer wrote), boot the target
# disk WITHOUT the ISO, and confirm the installed Ubuntu reaches a login prompt.
# For an FDE install (#10), the disk is LUKS-encrypted, so the boot stops at a passphrase
# prompt on the serial; we inject the passphrase over a bidirectional pipe and then prove
# the system unlocks and reaches login.
ilog="$out/installed-serial.log"; : > "$ilog"
LUKSPASS="devos-luks-changeme"

if [ "${FDE:-0}" = "1" ]; then
  echo "FDE mode: will inject LUKS passphrase at the boot prompt"
  rm -f "$out/con.in" "$out/con.out"; mkfifo "$out/con.in" "$out/con.out"
  # Guest output -> log
  ( cat "$out/con.out" > "$ilog" ) &
  catp=$!
  # Hold the input pipe open; inject the passphrase once the prompt appears, unlocked=1 on success.
  ( exec 9>"$out/con.in"
    injected=0
    for _ in $(seq 1 60); do
      if [ "$injected" = 0 ] && grep -qiE "enter passphrase|passphrase for|unlock" "$ilog" 2>/dev/null; then
        printf '%s\n' "$LUKSPASS" >&9; injected=1
        echo "DEVOS_FDE_PASSPHRASE_SENT" >> "$ilog"
      fi
      sleep 3
    done ) &
  injp=$!
  timeout 480 qemu-system-x86_64 \
    -machine q35 -accel "$accel" -cpu max -m 2048 -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$code" \
    -drive if=pflash,format=raw,file="$out/OVMF_VARS.fd" \
    -drive file="$out/target.qcow2",if=virtio,format=qcow2 \
    -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
    -display none -serial pipe:"$out/con" &
  ip=$!
  lok=0
  for _ in $(seq 1 48); do
    if grep -qE "devos login:|login:" "$ilog" 2>/dev/null; then lok=1; break; fi
    kill -0 "$ip" 2>/dev/null || break
    sleep 10
  done
  kill "$ip" "$catp" "$injp" 2>/dev/null || true; wait "$ip" 2>/dev/null || true
  echo "---- installed-system serial tail ----"; tail -40 "$ilog" 2>/dev/null || true
  echo "--------------------------------------"
  if [ "$lok" = 1 ] && grep -q "DEVOS_FDE_PASSPHRASE_SENT" "$ilog" 2>/dev/null; then
    echo "FDE UNLOCK PASSED: LUKS passphrase accepted and the encrypted system booted to login."
  else
    echo "FDE UNLOCK FAILED: encrypted system did not unlock+reach login."
    exit 1
  fi
else
  timeout 420 qemu-system-x86_64 \
    -machine q35 -accel "$accel" -cpu max -m 2048 -smp 2 \
    -drive if=pflash,format=raw,readonly=on,file="$code" \
    -drive if=pflash,format=raw,file="$out/OVMF_VARS.fd" \
    -drive file="$out/target.qcow2",if=virtio,format=qcow2 \
    -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
    -display none -serial file:"$ilog" &
  ip=$!
  lok=0
  for _ in $(seq 1 42); do
    if grep -qE "devos login:|login:" "$ilog" 2>/dev/null; then lok=1; break; fi
    kill -0 "$ip" 2>/dev/null || break
    sleep 10
  done
  kill "$ip" 2>/dev/null || true; wait "$ip" 2>/dev/null || true
  echo "---- installed-system serial tail ----"; tail -30 "$ilog" 2>/dev/null || true
  echo "--------------------------------------"
  if [ "$lok" = 1 ]; then
    echo "REBOOT->LOGIN PASSED: the installed DevOS system boots to a login prompt."
  else
    echo "REBOOT->LOGIN FAILED: installed system did not reach a login prompt."
    exit 1
  fi
fi
