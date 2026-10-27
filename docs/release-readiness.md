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
Engineering gates: **DONE**. The remaining Beta gates are human/hardware.
- [x] Installer install→reboot→login verified — green (REBOOT->LOGIN / FDE boot to login)
- [x] OS upgrade applied + rebooted verified — green (DEVOS_UPGRADE_OK)
- [x] FDE: encrypted install + unlock verified — green (FDE UNLOCK PASSED, v0.1.0-alpha6 cycle)
- [x] CVE scan runs and attaches (`trivy-vuln.txt`) — **triage of findings is a human step** (do before Beta)
- [ ] Per-package license review **signed off** (inventory done: `license-inventory.tsv`; sign-off is human)
- [ ] Real-hardware smoke test on **≥2 physical machines** (gap #6) — **needs hardware**
- [ ] ≥2 active maintainers (gap #9) — **needs people**

**Beta blockers remaining: 3 (+1 triage)** — all human/hardware, none code:
license sign-off, hardware smoke test, a second maintainer, and a written CVE-triage note.

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
| Beta | engineering-ready 2026-10-27 | (provisional) | v0.1.0-alpha6 + CI; 3 human/hardware gates remain |
| Stable | — | — | — |

> No automated process can tick the Beta/Stable hardware, legal, funding, people, and human-QA
> boxes. Those are the irreducible human gate to production.
