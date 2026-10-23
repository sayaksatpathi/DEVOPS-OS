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
# §11 reproducible build: derive a stable timestamp from the source commit so tools that
# honor SOURCE_DATE_EPOCH don't embed the wall-clock build time.
export SOURCE_DATE_EPOCH="$(git -C "$here" log -1 --format=%ct 2>/dev/null || date +%s)"
echo "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH"
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
# Headroom: GNOME desktop adds ~2 GB, so grow more when a desktop profile is requested.
# qcow2 is sparse + the final image is compressed, so extra virtual size costs little.
case ",$PROFILES," in
  *,desktop,*) qemu-img resize "$out/devos.qcow2" +12G ;;
  *)           qemu-img resize "$out/devos.qcow2" +4G ;;
esac
export LIBGUESTFS_BACKEND="${LIBGUESTFS_BACKEND:-direct}"
virt-customize -a "$out/devos.qcow2" \
  --copy-in "$out/devos-src.tar.gz:/opt" \
  --run-command 'mkdir -p /opt/devos && tar xzf /opt/devos-src.tar.gz -C /opt/devos' \
  --write "/etc/devos-release:DevOS experimental cloud image; profiles=${PROFILES}; base=${BASE_FILE}"

echo "== [4/6] provision by booting (cloud-init runs devos apply; network works here) =="
# §8 strict reproducibility: if DEVOS_APT_SNAPSHOT=<YYYYMMDDTHHMMSSZ> is set, pin apt to
# snapshot.ubuntu.com at that timestamp (deb822 Snapshot field) so installs are time-stable.
if [ -n "${DEVOS_APT_SNAPSHOT:-}" ]; then
  snap_cmd="[ bash, -c, \"printf 'Snapshot: %s\\\\n' '${DEVOS_APT_SNAPSHOT}' >> /etc/apt/sources.list.d/ubuntu.sources && echo DEVOS_APT_SNAPSHOT_${DEVOS_APT_SNAPSHOT} > /dev/ttyS0\" ]"
  echo "APT snapshot pin: ${DEVOS_APT_SNAPSHOT}"
else
  snap_cmd='[ bash, -c, "true" ]'
fi
sed -e "s/__PROFILES__/${PROFILES//,/ }/g" -e "s|  - __SNAPSHOT__|  - ${snap_cmd}|" \
  image/seed/provision-user-data > "$out/prov-user-data"
cp image/seed/meta-data "$out/prov-meta-data"
cloud-localds "$out/prov-seed.iso" "$out/prov-user-data" "$out/prov-meta-data"
bash image/run-vm.sh "$out/devos.qcow2" "$out/prov-seed.iso" "DEVOS_PROVISION_OK" 1800 \
  || { echo "ERROR: provisioning boot did not reach success marker"; exit 1; }

# In-image idempotency (gap #2): a second apply must report no changes.
if grep -q "DEVOS_IDEMPOTENT_FAIL" "$out/serial.log"; then
  echo "ERROR: in-image re-apply changed state — not idempotent"; exit 1
fi
grep -q "DEVOS_IDEMPOTENT_OK" "$out/serial.log" \
  && echo "in-image idempotency: OK (second apply changed=0)" \
  || echo "warn: idempotency marker not observed"

# Package SBOM (gap #10): copy the installed-package inventory out of the image (offline).
virt-copy-out -a "$out/devos.qcow2" /var/lib/devos/packages.tsv "$out/" 2>/dev/null \
  && echo "SBOM package inventory extracted" || echo "warn: SBOM copy-out failed"
# SBOM completeness: binary tools + the devos engine (not just apt packages).
virt-copy-out -a "$out/devos.qcow2" /var/lib/devos/extra-components.tsv "$out/" 2>/dev/null \
  && echo "SBOM extra components extracted" || echo "warn: extra-components copy-out failed"

# Hardening (hole #4/#5) must have applied.
if grep -q "DEVOS_HARDEN_FAIL" "$out/serial.log"; then
  echo "ERROR: image hardening failed"; exit 1
fi
grep -q "DEVOS_HARDENED_OK" "$out/serial.log" && echo "image hardening: OK" || echo "warn: hardening marker not seen"
# Container smoke test (hole #7) — soft (needs registry network during provisioning).
grep -q "DEVOS_CONTAINER_RUN_OK" "$out/serial.log" && echo "container run: OK" \
  || echo "note: container-run marker not seen (profile may lack podman, or registry unreachable)"

echo "== [5/6] image hygiene (clear cloud-init state, reset machine identity) =="
virt-customize -a "$out/devos.qcow2" \
  --run-command 'cloud-init clean --logs || true' \
  --run-command 'rm -f /opt/devos-src.tar.gz'   # remove builder source tarball (keep /opt/devos)
virt-sysprep -a "$out/devos.qcow2" \
  --operations machine-id,ssh-hostkeys,logfiles,tmp-files,bash-history,crash-data

echo "== [5b/6] VERIFY image hygiene (prove no identity/secrets leak) =="
bash image/verify-hygiene.sh "$out/devos.qcow2"

echo "== [6/6] finalize (compress to fit release asset limits + smaller download) =="
qemu-img convert -O qcow2 -c "$out/devos.qcow2" "$out/devos.final.qcow2"
mv -f "$out/devos.final.qcow2" "$out/devos.qcow2"
qemu-img info "$out/devos.qcow2"
( cd "$out" && sha256sum devos.qcow2 | tee devos.qcow2.sha256 )
# §12 performance budget: record + enforce a compressed-image-size budget.
size_bytes="$(stat -c%s "$out/devos.qcow2")"
size_mb=$(( size_bytes / 1048576 ))
budget_mb="${DEVOS_IMAGE_BUDGET_MB:-1800}"
case ",$PROFILES," in *,desktop,*) budget_mb="${DEVOS_IMAGE_BUDGET_MB:-4096}" ;; esac
printf 'image_size_mb=%s\nbudget_mb=%s\nprofiles=%s\nsource_date_epoch=%s\n' \
  "$size_mb" "$budget_mb" "$PROFILES" "$SOURCE_DATE_EPOCH" | tee "$out/perf-budget.txt"
if [ "$size_mb" -gt "$budget_mb" ]; then
  echo "PERF BUDGET EXCEEDED: image ${size_mb}MB > ${budget_mb}MB"; exit 1
fi
echo "perf budget OK (${size_mb}MB <= ${budget_mb}MB)"
echo "built: $out/devos.qcow2"
