# Production Readiness TODO (11 items)

Status: `done` · `automatable-wip` · `artifact-done-human-needed` · `blocked-external`.
"artifact-done-human-needed" = everything code can do is done; a human/hardware step remains.

## Automatable (code closes these)
1. **OS-upgrade automated test** — `done` ✅ — applies `apt full-upgrade` in-guest (holds
   cloud-init to avoid self-disruption), fixes half-config, confirms zero non-held packages
   remain upgradable. Verified green (DEVOS_UPGRADE_OK).
2. **Installer reboot→login** — `automatable-wip` — verifying in CI.
3. **FDE unlock-at-boot** — `done` ✅ — encrypted install + serial passphrase injection + cryptsetup unlock + boot-to-login, verified green (FDE UNLOCK PASSED).

## Supply chain
4. **CVE scan** — `done` — SBOM attached; Trivy version fixed (attaches on release).
5. **Per-package license inventory** — `artifact-done-human-needed` — auto-generate license list from the image; human sign-off remains.

## Structural / governance (code makes ready; human executes)
6. **Real-hardware validation** — `artifact-done-human-needed` — `tests/hardware/collect.sh` harness + matrix; needs physical machines.
7. **Trademark clearance** — `blocked-external` — filing checklist + search done; legal filing is the owner's.
8. **Funded security SLA** — `artifact-done-human-needed` — concrete SLA numbers written; "funded" is organizational.
9. **Co-maintainers / bus factor** — `artifact-done-human-needed` — MAINTAINERS.md + call-for-maintainers; real people required.
10. **Stable-release sign-off** — `artifact-done-human-needed` — release-readiness gate checklist; the sign-off is the owner's.

## Human QA
11. **Accessibility / audio / printing** — `artifact-done-human-needed` — automated a11y presence check + manual test checklist; real QA needs a human + hardware.
12. **Installer UX (partitioning + credentials)** — `artifact-done-human-needed` — guided/FDE variants + documented interactive path.

> Honest note: items 6–12 cannot be *fully* closed by writing code — they need physical hardware,
> legal action, funding, people, or human judgment. This file tracks them to the furthest point
> software can reach; the final step on each is explicitly a human one.
