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

**Preliminary search (2026-10-22, informal — NOT a legal clearance):** no registered trademark for
"DevOS" as an operating system was found; several **"DEVOPS"** marks exist (e.g. "DEVOPS STUDIO")
but none is "DevOS". A **defunct 2006 hobbyist OS** also used the name "DevOS" (Omnimaga forum), so
there is prior unregistered use. Net: lower registered-mark conflict than feared, but **"DevOS" is
generic and the `.com`/common domains are likely taken**; a formal registry search (USPTO/EUIPO/WIPO)
and a distinctiveness/counsel review are still required before public branding. Keep the name
*provisional* (it is, in README/DECISIONS/ADR-0012). This informal search does not substitute for
clearance, which only the project owner/counsel can perform.

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

## Ubuntu archive-component allowlist (master-prompt §7.1.1)

Default to the **smallest** component set. Current policy for Alpha images:

| Component | Policy | Rationale |
|---|---|---|
| `main` | allowed | Canonical-maintained, redistributable |
| `restricted` | **not enabled by default** | proprietary drivers/firmware need per-package review |
| `universe` | allowed, **per-package review** for anything DevOS adds | community-maintained; licenses vary |
| `multiverse` | **not enabled by default** | non-free; needs explicit approval |
| `restricted-extras`, non-free codecs, proprietary firmware | **not by default** | licensing + redistribution review required |

Profiles currently pull only from `main`/`universe` (e.g. `jq` is universe). OpenTofu (infra) is
MPL-2.0 from upstream, not the archive. Any new package from `restricted`/`multiverse` requires a
documented inclusion decision here before it ships in an image.

## Signing & provenance

Release images are **not** signed with a long-lived production key (deliberately — see
[`DECISIONS.md`](../DECISIONS.md)). Instead the pipeline uses **keyless Sigstore/cosign signing**
and **GitHub build-provenance attestations**, which bind each artifact to the exact workflow run
that built it without any secret-key custody. Verification instructions are in the release notes.
A dedicated production signing key (with HSM custody, rotation, revocation) remains a future
decision, required only if offline/air-gapped verification without Sigstore is needed.
