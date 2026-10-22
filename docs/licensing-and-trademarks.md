# Licensing and Trademarks

## Project license

DevOS's own code and documentation are licensed **Apache-2.0** ([`LICENSE`](../LICENSE)).
A distributed **image** is a different matter: it contains Ubuntu and third-party software,
each under its own license. Redistributing an image carries those obligations (see below).

## Trademark status — `DevOS` / `DEVOPS-OS` (PROVISIONAL, not cleared)

> **The name is not trademark-cleared and must not be treated as final branding.** "DevOS"
> is a short, generic-sounding term; conflicts are likely across software and other sectors.
> A formal clearance is required before any public *branding* or stable release.

**What is NOT yet done (requires action by the project owner — I cannot perform legal clearance):**

1. **Trademark search** — a knock-out search of the relevant registries for "DevOS" and
   "DEVOPS-OS" in the goods/services classes that matter (Class 9 software, Class 42 SaaS):
   - US: USPTO TESS (https://tmsearch.uspto.gov/)
   - EU: EUIPO eSearch (https://euipo.europa.eu/eSearch/)
   - WIPO Global Brand Database (https://branddb.wipo.int/)
2. **Common-law / in-use search** — web + app stores + package registries (PyPI, npm, Docker
   Hub, GitHub org names) for existing projects or products using the name.
3. **Domain availability** — the `.org`/`.io`/`.dev` you'd want for the project.
4. **Ubuntu/Canonical remix & trademark policy** — a derivative must comply with Canonical's
   IP policy (https://ubuntu.com/legal/intellectual-property-policy) and trademark guidelines
   before using "Ubuntu" marks or implying endorsement. DevOS must not imply it is Ubuntu or
   is endorsed by Canonical.

**Preliminary assessment:** treat "DevOS" as high-conflict-risk and plan to either (a) clear a
more distinctive name, or (b) obtain counsel's opinion before public launch. Keep the name
marked *provisional* everywhere until then (it already is, in README/DECISIONS).

## Image redistribution — license obligations to satisfy before a public image release

A DevOS image bundles third-party software. Before publishing an image as anything other than
an experimental artifact, inventory and satisfy:

| Component class | Obligation | Status |
|---|---|---|
| Ubuntu base (main) | Canonical IP/redistribution policy; GPL/LGPL source availability | not reviewed |
| `universe`/`multiverse` packages | per-package license review; some non-free | allowlist not finalized |
| Fonts / icons / wallpapers | redistribution terms per asset | n/a yet (no desktop assets) |
| OpenTofu (infra profile) | MPL-2.0 (OpenTofu) — redistribution OK with notice | OK to bundle |
| Firmware / codecs | per-package review; many non-free | none bundled by default |

Action: produce a full SBOM of the shipped image (the release pipeline attaches build provenance
and an image manifest; a per-package SBOM/license scan is the next step), and keep a NOTICE file
of attributions for any redistributed GPL/MPL/BSD components.

## Signing & provenance

Release images are **not** signed with a long-lived production key (deliberately — see
[`DECISIONS.md`](../DECISIONS.md)). Instead the pipeline uses **keyless Sigstore/cosign signing**
and **GitHub build-provenance attestations**, which bind each artifact to the exact workflow run
that built it without any secret-key custody. Verification instructions are in the release notes.
A dedicated production signing key (with HSM custody, rotation, revocation) remains a future
decision, required only if offline/air-gapped verification without Sigstore is needed.
