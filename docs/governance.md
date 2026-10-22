# Governance, Support & Release Lifecycle

Master-prompt §14. Honest and modest: this is a volunteer, pre-Alpha project; nothing here
promises more than maintainers can deliver. Last updated 2026-10-22 (gap #13).

## Project status & maturity
**Pre-Alpha / experimental.** No stable release exists. Images are unsigned-for-production
(keyless Sigstore only) and must be run in disposable VMs. Not for production use.

## Versioning
- Scheme: `v<MAJOR>.<MINOR>.<PATCH>-<pre>` (e.g. `v0.1.0-alpha2`). Pre-1.0 = no stability promise.
- Image tags also record the base Ubuntu point-release they were built from.

## Maturity gates (what must be true to advance)
| Stage | Bar |
|---|---|
| **Alpha** (now) | Reproducible build; VM boot + install verified; signed/attested artifacts; honest docs. |
| **Beta** | Full install→reboot→login verified; Secure Boot verified; failure-injection (VM) green; SBOM + license review; real-hardware smoke tests on ≥2 machines. |
| **Stable** | Recovery/rollback tested; update/upgrade path tested; security response process exercised; support policy funded; trademark cleared. |

## Support policy (provisional)
- Support **tracks the Ubuntu base** (26.04 → standard maintenance ~5 years upstream), but DevOS
  itself guarantees nothing beyond best-effort while maintained.
- Security fixes: best-effort, coordinated disclosure (see SECURITY.md). **No SLA is promised**
  that volunteers cannot meet; a real SLA is a Stable-gate item.
- EOL: a DevOS release is EOL when its Ubuntu base leaves standard maintenance, or sooner if
  unmaintained. EOL will be announced in CHANGELOG + releases.

## Maintainers & continuity
- Current maintainer: project owner (`sayaksatpathi`). **Bus factor = 1** — a continuity risk;
  adding co-maintainers is a Beta-gate goal. Maintainer actions: review PRs, cut releases, triage
  security reports.
- Decision process: material changes via ADR (docs/adr) + DECISIONS.md; PRs require green CI.

## Release process
1. Land changes on `main` (CI green: tests, validation, secret scan).
2. Tag `vX.Y.Z-preN` → CI builds image, boot-tests, signs (Sigstore), attests provenance,
   publishes a **prerelease** with the image + checksum + signature + manifest.
3. Record in CHANGELOG; never mutate a published release (cut a new tag instead).

## What is explicitly NOT yet governed (and must be before Stable)
Funded security SLA · formal CoC enforcement contacts · co-maintainer roster · trademark/brand ·
production signing-key custody · a tested deprecation/migration policy.
