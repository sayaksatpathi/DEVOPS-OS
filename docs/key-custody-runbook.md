# Archive Signing Key — Custody Runbook (§17)

Image signing uses keyless Sigstore (no key to custody). The **apt repository** needs a
long-lived GPG key — this is the runbook for it.

## Generate (offline machine)
```bash
gpg --batch --gen-key <<KEY
%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Name-Real: DevOS Archive Signing Key
Name-Email: archive@devos.example
Expire-Date: 2y
KEY
gpg --armor --export > devos-archive-keyring.asc   # public; ship to clients
gpg --export-secret-keys > devos-archive.sec        # PRIVATE — store in HSM/secret mgr
```

## Custody
- Private key lives in an **HSM** or a tightly-scoped CI secret (`DEVOS_REPO_GPG_KEY`), never in git.
- Access limited to release owners; every use is logged.
- Public key published at a stable URL + shipped as `/usr/share/keyrings/devos-archive-keyring.gpg`.

## Rotation / revocation
- Rotate before the 2-year expiry; publish the new public key alongside the old for overlap.
- On compromise: revoke (`gpg --gen-revoke`), publish the revocation, re-sign the repo with a
  new key, and issue an advisory (ties to SECURITY.md).

## Still operator decisions (not code)
HSM procurement, CI-secret setup, the mirror/CDN that hosts `dists/`+`pool/`, and bandwidth cost.
