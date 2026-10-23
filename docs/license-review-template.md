# License Review & Sign-off (§15) — TEMPLATE

The inventory is automated (`tools/license-inventory.sh`, plus the Trivy license scan in CI
and the SBOM). The **review and sign-off below is a human/legal step** — code can list
licenses, it cannot clear them.

## Inputs
- `license-inventory.tsv` (per-package license)
- `devos-*.sbom.cdx.json` (release SBOM)
- Trivy `licenses.txt` (release asset)

## Review checklist (reviewer fills in)
- [ ] No license in a **deny list** (e.g. strong-copyleft where incompatible with distribution intent)
- [ ] All **GPL/LGPL** source-offer obligations satisfiable (we ship/point to source)
- [ ] `restricted`/`multiverse` components explicitly approved (codecs, firmware, fonts)
- [ ] Redistribution of Ubuntu base complies with Canonical's IP policy (remix terms)
- [ ] Firmware blobs + their licenses enumerated and acceptable
- [ ] Attribution/NOTICE file assembled

## Sign-off
| Reviewer | Role | Date | Decision |
|---|---|---|---|
|  | legal/maintainer |  | approve / changes-needed |

> No automation can sign this. It gates a Stable release (docs/release-readiness.md).
