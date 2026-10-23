"""Supply-chain verification for binary artifacts (master prompt §9.1).

A checksum copied from the same unauthenticated page as the download is
trust-on-first-use and is NOT a trust signal on its own. The engine therefore
distinguishes:

- checksum verification (integrity): the file matches an expected SHA-256.
- signature verification (authenticity): an upstream-published signature over the
  artifact or its checksum file, verified against a pinned key.

This module implements the integrity check and the policy gate. Signature
verification shells out to the platform tool (gpg/cosign) and is represented here
by a policy function so the engine can refuse to install an unverifiable binary
rather than silently trusting it. No network access happens here; callers pass
already-downloaded paths.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path, _chunk: int = 1 << 20) -> str:
    """Return the lowercase hex SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(_chunk), b""):
            h.update(block)
    return h.hexdigest()


def verify_checksum(path: str | Path, expected: str) -> bool:
    """True iff the file's SHA-256 matches ``expected`` (accepts a 'sha256:' prefix)."""
    want = expected.split(":", 1)[1] if expected.lower().startswith("sha256:") else expected
    return sha256_file(path).lower() == want.strip().lower()


def install_allowed(verification: dict) -> tuple[bool, str]:
    """Policy gate: may a binary tool be installed from its lockfile verification block?

    Returns (allowed, reason). Enforces §9.1: a checksum alone (no signature/attestation)
    is only acceptable when an explicit, documented fallback has been approved.
    """
    if not isinstance(verification, dict):
        return False, "no verification block"
    method = verification.get("method")
    if not verification.get("checksum"):
        return False, "no checksum recorded"
    if method == "upstream-signature":
        # A real signature requires signature material to actually verify (not a label).
        # Two accepted cosign modes:
        #  - "sums": cosign-verify a SHA256SUMS file, then checksum the artifact against it.
        #  - "blob": cosign-verify the artifact blob directly (.sig + .cert).
        ident = verification.get("certIdentityRegexp") or verification.get("certIdentity")
        issuer = verification.get("certOidcIssuer")
        has_sums = all(verification.get(k) for k in ("sumsUrl", "sigUrl", "certUrl"))
        has_blob = all(verification.get(k) for k in ("blobSigUrl", "blobCertUrl"))
        if not (ident and issuer):
            return False, "upstream-signature missing cert identity/issuer (would be TOFU)"
        if has_sums:
            return True, "upstream-signature (cosign sums) + checksum"
        if has_blob:
            return True, "upstream-signature (cosign blob) + checksum"
        return False, "upstream-signature missing sums or blob material (would be TOFU)"
    if method == "attestation":
        return True, f"{method} + checksum"
    if method == "fallback":
        if verification.get("fallbackApproved") is True and verification.get("residualRisk"):
            return True, "approved fallback (residual risk accepted)"
        return False, "fallback requires fallbackApproved=true and residualRisk"
    return False, f"unrecognized verification method: {method!r}"
