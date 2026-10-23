# Signing & Distribution Infrastructure (§17)

What code provides here, and what remains an operator decision (money/custody).

## Image signing — DONE
Release images are signed with **Sigstore cosign (keyless, OIDC)** and carry a provenance
attestation + SBOM. No long-lived key to leak. Verify with the identity in the install guide.

## APT repository — CONFIG PROVIDED
`packaging/apt-repo/` builds a **GPG-signed** apt repo with reprepro
(`build-apt-repo.sh <deb-dir> <keyid>`). The repo tree (`dists/`, `pool/`) is then published
to a mirror/CDN. Clients trust it via a `signed-by` keyring.

## Operator decisions (NOT code)
- **Repo GPG key custody**: generate an archive-signing key, store it in an **HSM or a CI
  secret with tight access**, define rotation + a revocation/compromise runbook.
- **Hosting & cost owner**: mirror/CDN for images + apt repo, bandwidth budget, retention.
- **Publication gate**: who approves a public release (ties to docs/release-readiness.md).
- **Key for offline verification**: Sigstore covers online verification; if offline/air-gapped
  verification is required, additionally sign with an HSM-backed long-lived key.

## Status
Image signing is production-grade. The apt-repo mechanism is ready; **hosting, key custody,
and the publication gate are yours** — they need infrastructure and money, not code.
