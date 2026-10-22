#!/usr/bin/env bash
# Build a bootable DevOS cloud image (qcow2) from the official Ubuntu 26.04 cloud image.
# Approach: copy the DevOS source into the image offline (no appliance network, which is
# unreliable on CI), then PROVISION by booting the image in QEMU where qemu user-mode
# networking provides working DNS — cloud-init runs `devos profile apply` on first boot,
# baking the tools into the disk. Finally reset per-machine identity. Never touches the
# host disk.
set -euo pipefail

PROFILES="${1:-core}"
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
# shellcheck disable=SC1091
source image/base-image.env
out="image/out"
mkdir -p "$out"

echo "== [1/6] download official base cloud image =="
curl -fL --retry 3 "$BASE_URL" -o "$out/$BASE_FILE"
curl -fL --retry 3 "$BASE_SHA256SUMS_URL" -o "$out/SHA256SUMS"

echo "== [2/6] verify base against official SHA256SUMS =="
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

echo "== [3/6] copy DevOS source into the image (offline) =="
tar czf "$out/devos-src.tar.gz" --exclude=.git --exclude='image/out' .
cp "$out/$BASE_FILE" "$out/devos.qcow2"
qemu-img resize "$out/devos.qcow2" +6G
export LIBGUESTFS_BACKEND="${LIBGUESTFS_BACKEND:-direct}"
virt-customize -a "$out/devos.qcow2" \
  --copy-in "$out/devos-src.tar.gz:/opt" \
  --run-command 'mkdir -p /opt/devos && tar xzf /opt/devos-src.tar.gz -C /opt/devos' \
  --write "/etc/devos-release:DevOS experimental cloud image; profiles=${PROFILES}; base=${BASE_FILE}"

echo "== [4/6] provision by booting (cloud-init runs devos apply; network works here) =="
sed "s/__PROFILES__/${PROFILES//,/ }/g" image/seed/provision-user-data > "$out/prov-user-data"
cp image/seed/meta-data "$out/prov-meta-data"
cloud-localds "$out/prov-seed.iso" "$out/prov-user-data" "$out/prov-meta-data"
bash image/run-vm.sh "$out/devos.qcow2" "$out/prov-seed.iso" "DEVOS_PROVISION_OK" 1200 \
  || { echo "ERROR: provisioning boot did not reach success marker"; exit 1; }

echo "== [5/6] image hygiene (clear cloud-init state, reset machine identity) =="
virt-customize -a "$out/devos.qcow2" --run-command 'cloud-init clean --logs || true'
virt-sysprep -a "$out/devos.qcow2" \
  --operations machine-id,ssh-hostkeys,logfiles,tmp-files,bash-history,crash-data

echo "== [6/6] finalize =="
qemu-img info "$out/devos.qcow2"
( cd "$out" && sha256sum devos.qcow2 | tee devos.qcow2.sha256 )
echo "built: $out/devos.qcow2"
