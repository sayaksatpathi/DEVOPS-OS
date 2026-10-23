#!/usr/bin/env bash
# §17 Build a GPG-signed apt repository from .deb packages using reprepro.
# Hosting (mirror/CDN) and GPG key custody are the operator's responsibility — see
# docs/signing-infrastructure.md. This script only produces the signed repo tree.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
pkgdir="${1:?usage: build-apt-repo.sh <dir-of-.deb> [keyid]}"
keyid="${2:-${DEVOS_REPO_GPG_KEYID:?set DEVOS_REPO_GPG_KEYID or pass keyid}}"
command -v reprepro >/dev/null || { echo "install reprepro"; exit 1; }
sed -i "s/__DEVOS_REPO_GPG_KEYID__/${keyid}/" "$here/conf/distributions"
for deb in "$pkgdir"/*.deb; do
  [ -e "$deb" ] || { echo "no .deb in $pkgdir"; exit 1; }
  reprepro -b "$here" includedeb devos "$deb"
done
echo "Signed repo built at $here. Publish 'dists/' and 'pool/' to your mirror/CDN."
echo "Clients add:  deb [signed-by=/usr/share/keyrings/devos-archive-keyring.gpg] <URL> devos main"
