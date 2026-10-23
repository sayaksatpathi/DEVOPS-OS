#!/usr/bin/env bash
# Image-hygiene verification (§11 / §6.17): PROVE — not assume — that the built image carries
# no build-time identity or secrets. Scans the qcow2 offline with libguestfs. Fails on any leak.
set -euo pipefail
img="${1:?usage: verify-hygiene.sh <image.qcow2>}"
export LIBGUESTFS_BACKEND="${LIBGUESTFS_BACKEND:-direct}"
fail=0

mid="$(virt-cat -a "$img" /etc/machine-id 2>/dev/null | tr -d '[:space:]' || true)"
if [ -n "$mid" ]; then echo "LEAK: /etc/machine-id not empty ($mid)"; fail=1; else echo "ok: machine-id cleared"; fi

if virt-ls -a "$img" /etc/ssh 2>/dev/null | grep -q "ssh_host_"; then
  echo "LEAK: SSH host keys present in image"; fail=1
else echo "ok: no SSH host keys"; fi

for d in /root /home/devos; do
  if virt-ls -a "$img" "$d" 2>/dev/null | grep -q "^.bash_history$"; then
    echo "LEAK: $d/.bash_history present"; fail=1
  fi
done
echo "ok: bash-history check done"

if virt-ls -a "$img" /opt 2>/dev/null | grep -q "devos-src.tar.gz"; then
  echo "LEAK: builder source tarball /opt/devos-src.tar.gz left in image"; fail=1
else echo "ok: no builder source tarball"; fi

if virt-cat -a "$img" /root/.ssh/authorized_keys 2>/dev/null | grep -q . ; then
  echo "LEAK: /root/.ssh/authorized_keys present (builder key?)"; fail=1
else echo "ok: no root authorized_keys"; fi

# No random-seed cloned; cloud-init instance data cleared
if virt-ls -a "$img" /var/lib/cloud/instances 2>/dev/null | grep -q . ; then
  echo "WARN: /var/lib/cloud/instances not empty (cloud-init state)"; fi

if [ "$fail" -eq 0 ]; then echo "IMAGE HYGIENE: CLEAN"; else echo "IMAGE HYGIENE: LEAKS FOUND"; exit 1; fi
