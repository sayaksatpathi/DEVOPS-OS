#!/usr/bin/env bash
# Build a bootable DevOS cloud image (qcow2) from the official Ubuntu 26.04 cloud image
# by baking in the selected DevOS profiles with the same devos/Ansible engine used
# everywhere else. Runs on a Linux builder (CI or a VM). Never touches the host disk.
set -euo pipefail

PROFILES="${1:-core}"
here="$(cd "$(dirname "$0")/.." && pwd)"   # repo root
cd "$here"
# shellcheck disable=SC1091
source image/base-image.env
out="image/out"
mkdir -p "$out"

echo "== [1/6] download official base cloud image =="
curl -fL --retry 3 "$BASE_URL" -o "$out/$BASE_FILE"
curl -fL --retry 3 "$BASE_SHA256SUMS_URL" -o "$out/SHA256SUMS"

echo "== [2/6] verify base against official SHA256SUMS =="
# Best-effort GPG authenticity of SHA256SUMS (warn, don't fail, on a dev build).
if curl -fL --retry 3 "$BASE_SHA256SUMS_GPG_URL" -o "$out/SHA256SUMS.gpg" 2>/dev/null; then
  if command -v gpg >/dev/null 2>&1 && \
     gpg --batch --keyserver hkps://keyserver.ubuntu.com \
         --recv-keys "$UBUNTU_CLOUDIMAGE_KEY_FPR" 2>/dev/null; then
    if gpg --batch --verify "$out/SHA256SUMS.gpg" "$out/SHA256SUMS" 2>/dev/null; then
      echo "   SHA256SUMS GPG signature: OK"
    else
      echo "   WARNING: SHA256SUMS GPG verification failed (continuing dev build)"
    fi
  else
    echo "   WARNING: could not fetch Ubuntu signing key (continuing dev build)"
  fi
fi
want="$(grep -E "[ *]${BASE_FILE}\$" "$out/SHA256SUMS" | awk '{print $1}' | head -1)"
[ -n "$want" ] || { echo "ERROR: $BASE_FILE not listed in SHA256SUMS"; exit 1; }
echo "${want}  $out/$BASE_FILE" | sha256sum -c -

echo "== [3/6] assemble DevOS source tarball =="
tar czf "$out/devos-src.tar.gz" --exclude=.git --exclude='image/out' .

echo "== [4/6] customize image with profiles: ${PROFILES} =="
cp "$out/$BASE_FILE" "$out/devos.qcow2"
qemu-img resize "$out/devos.qcow2" +6G
export LIBGUESTFS_BACKEND="${LIBGUESTFS_BACKEND:-direct}"
# Prefer slirp networking: the newer 'passt' backend fails on some CI runners.
export LIBGUESTFS_BACKEND_SETTINGS="${LIBGUESTFS_BACKEND_SETTINGS:-network=slirp}"
virt-customize -a "$out/devos.qcow2" --network \
  --copy-in "$out/devos-src.tar.gz:/opt" \
  --run-command 'mkdir -p /opt/devos && tar xzf /opt/devos-src.tar.gz -C /opt/devos' \
  --run-command 'rm -f /etc/resolv.conf; printf "nameserver 10.0.2.3\nnameserver 1.1.1.1\n" > /etc/resolv.conf' \
  --run-command 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ansible-core python3' \
  --run-command "cd /opt/devos && for p in ${PROFILES//,/ }; do PYTHONPATH=packages/cli DEVOS_ROOT=/opt/devos python3 -m devos profile apply \$p --confirm; done" \
  --run-command "cd /opt/devos && for p in ${PROFILES//,/ }; do PYTHONPATH=packages/cli DEVOS_ROOT=/opt/devos python3 -m devos profile lock \$p || true; done" \
  --write "/etc/devos-release:DevOS experimental cloud image; profiles=${PROFILES}; base=${BASE_FILE}"

echo "== [5/6] image hygiene (reset machine identity, clear build state) =="
virt-sysprep -a "$out/devos.qcow2" \
  --operations machine-id,ssh-hostkeys,logfiles,tmp-files,bash-history,crash-data

echo "== [6/6] finalize =="
qemu-img info "$out/devos.qcow2"
( cd "$out" && sha256sum devos.qcow2 | tee devos.qcow2.sha256 )
echo "built: $out/devos.qcow2"
