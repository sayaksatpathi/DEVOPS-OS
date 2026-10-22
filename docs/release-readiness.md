# Release-Readiness Gate (Alpha → Beta → Stable)

The checklist that must be satisfied — and **signed off by a human maintainer** — before a
release may claim each maturity level. Code can make every item *verifiable*; it cannot sign
off Stable. That signature is the owner's (gap #10).

## Alpha (current) — all ✅
- [x] Reproducible build from source (CI)
- [x] Clean VM boot + install (QEMU/OVMF)
- [x] Enforced Secure Boot verified
- [x] Idempotent provisioning + independent reproducibility
- [x] Failure-injection (engine + VM) + backup/restore
- [x] Signed (Sigstore) + provenance attestation + SBOM
- [x] Honest docs (subsystem register, threat model, ADRs, governance)

## Beta — required before claiming Beta
- [ ] Installer install→reboot→login verified (gap #1, in progress)
- [ ] OS upgrade applied + rebooted verified (gap #4, in progress)
- [ ] FDE: encrypted install + unlock verified (gap #2/#3)
- [ ] CVE scan green with a documented triage of findings
- [ ] Per-package license review signed off (gap #5/#10)
- [ ] Real-hardware smoke test on **≥2 physical machines** (gap #6) — **needs hardware**
- [ ] ≥2 active maintainers (gap #9) — **needs people**

## Stable — required before claiming Stable / production
- [ ] Recovery/rescue walkthrough tested on hardware
- [ ] Security response exercised; **funded SLA** maintainers can meet (gap #8)
- [ ] Trademark cleared; non-provisional name (gap #7) — **legal**
- [ ] Accessibility/audio/printing QA passed (gap #11) — **needs human QA**
- [ ] Support/EOL policy funded and published
- [ ] **Maintainer sign-off** recorded here with date + evidence links

## Sign-off record
| Level | Date | Maintainer | Evidence |
|---|---|---|---|
| Alpha | 2026-10-22 | (provisional) | v0.1.0-alpha5 release + CI |
| Beta | — | — | — |
| Stable | — | — | — |

> No automated process can tick the Beta/Stable hardware, legal, funding, people, and human-QA
> boxes. Those are the irreducible human gate to production.
