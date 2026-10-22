#!/usr/bin/env bash
# Build a DevOS installer ISO: the official Ubuntu 26.04 live-server ISO with an
# embedded autoinstall config that installs Ubuntu and bakes in the selected DevOS
# profiles. The original boot setup (UEFI + BIOS) is preserved via xorriso replay.
set -euo pipefail

PROFILES="${1:-core}"
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
out="image/out"
mkdir -p "$out"

ISO_URL="https://releases.ubuntu.com/26.04/ubuntu-26.04-live-server-amd64.iso"
ISO_SUMS="https://releases.ubuntu.com/26.04/SHA256SUMS"
src="$out/ubuntu-live-server.iso"

echo "== [1/5] download official live-server ISO =="
curl -fL --retry 3 "$ISO_URL" -o "$src"
curl -fL --retry 3 "$ISO_SUMS" -o "$out/SHA256SUMS"

echo "== [2/5] verify ISO checksum =="
want="$(grep -E 'live-server-amd64.iso' "$out/SHA256SUMS" | awk '{print $1}' | head -1)"
[ -n "$want" ] || { echo "ERROR: live-server ISO not in SHA256SUMS"; exit 1; }
echo "${want}  ${src}" | sha256sum -c -

echo "== [3/5] build autoinstall seed + source tarball =="
pwhash="$(openssl passwd -6 devos)"
rm -rf "$out/nocloud"; mkdir -p "$out/nocloud"
sed -e "s|__PROFILES__|${PROFILES//,/ }|g" \
    -e "s|__PWHASH__|${pwhash//|/\\|}|g" \
    image/autoinstall/user-data > "$out/nocloud/user-data"
: > "$out/nocloud/meta-data"
tar czf "$out/devos-src.tar.gz" --exclude=.git --exclude='image/out' .

echo "== [4/5] patch grub.cfg to enable autoinstall =="
rm -f "$out/grub.cfg"
xorriso -osirrox on -indev "$src" -extract /boot/grub/grub.cfg "$out/grub.cfg"
# Append autoinstall params to each kernel line and shorten the menu timeout.
sed -i -E 's#(linux\s+/casper/vmlinuz[^\n]*)#\1 autoinstall ds=nocloud\\;s=/cdrom/nocloud/#' "$out/grub.cfg"
sed -i -E 's/set timeout=[0-9]+/set timeout=1/' "$out/grub.cfg"

echo "== [5/5] repack ISO (boot preserved) =="
iso="$out/devos-installer-amd64.iso"
xorriso -indev "$src" -outdev "$iso" \
  -boot_image any replay \
  -map "$out/grub.cfg" /boot/grub/grub.cfg \
  -map "$out/nocloud" /nocloud \
  -map "$out/devos-src.tar.gz" /devos-src.tar.gz \
  -end
( cd "$out" && sha256sum "$(basename "$iso")" | tee "$(basename "$iso").sha256" )
echo "built: $iso"
