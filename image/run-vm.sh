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

# Secure Boot mode (SECBOOT=1): use the secboot firmware + MS-keys-enrolled vars, so a
# successful boot proves the Ubuntu-signed chain works under Secure Boot.
if [ "${SECBOOT:-0}" = "1" ]; then
  code="$(ls /usr/share/OVMF/OVMF_CODE_4M.secboot.fd /usr/share/OVMF/OVMF_CODE.secboot.fd 2>/dev/null | head -1 || true)"
  varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.ms.fd /usr/share/OVMF/OVMF_VARS.ms.fd /usr/share/OVMF/OVMF_VARS_4M.fd 2>/dev/null | head -1 || true)"
  echo "Secure Boot mode: code=$code vars=$varstpl"
else
  code="$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd 2>/dev/null | head -1 || true)"
  varstpl="$(ls /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd 2>/dev/null | head -1 || true)"
fi
[ -n "$code" ] && [ -n "$varstpl" ] || { echo "ERROR: OVMF firmware not found (install 'ovmf')"; exit 1; }

vars="$out/OVMF_VARS.fd"; cp -f "$varstpl" "$vars"
log="$out/serial.log"; : > "$log"
accel="tcg"; [ -w /dev/kvm ] && accel="kvm"   # -accel takes a single value, not kvm:tcg

# Optional emulated TPM 2.0 (TPM=1) — proves the image boots with a vTPM present.
tpm_args=()
if [ "${TPM:-0}" = "1" ] && command -v swtpm >/dev/null 2>&1; then
  tpmdir="$out/swtpm"; mkdir -p "$tpmdir"
  swtpm socket --tpmstate dir="$tpmdir" --ctrl type=unixio,path="$tpmdir/sock" \
    --tpm2 --daemon --pid "$tpmdir/pid" 2>/dev/null || true
  tpm_args=(-chardev socket,id=chrtpm,path="$tpmdir/sock" \
            -tpmdev emulator,id=tpm0,chardev=chrtpm \
            -device tpm-tis,tpmdev=tpm0)
  echo "vTPM enabled"
fi

echo "booting $(basename "$img") (accel=$accel, SECBOOT=${SECBOOT:-0}, TPM=${TPM:-0}, timeout=${tmo}s), waiting for /$marker/"
timeout "$tmo" qemu-system-x86_64 \
  -machine q35${SECBOOT:+,smm=on} -accel "$accel" -cpu max -m 4096 -smp 2 \
  -global ICH9-LPC.disable_s3=1 \
  -drive if=pflash,format=raw,readonly=on,file="$code" \
  -drive if=pflash,format=raw,file="$vars" \
  "${tpm_args[@]}" \
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
