# Testing Strategy

Master-prompt §13. What is tested, where, and what remains. Last updated 2026-10-22.

## Test classes & status
| Class | Where | Status |
|---|---|---|
| Unit (schema, resolver, CLI, verify, failure-injection, fuzz) | host/CI | ✅ 63 tests passing |
| Malformed-input / parser fuzz | host/CI | ✅ 1000-iteration validator fuzz |
| Provisioning integration + idempotence | real Ubuntu (WSL) + in-image | ✅ WSL; ⏳ in-image idempotency check being added |
| Clean VM image boot/install | CI (QEMU/OVMF) | ✅ cloud + desktop boot; ✅ installer unattended install |
| Desktop reaches GNOME session | CI | ⏳ asserting gdm3/gnome-shell (gap #4) |
| Install → reboot → login | CI | ⏳ second-boot verification (gap #1) |
| Secure Boot | CI (secboot OVMF) | ⏳ being added (gap #5) |
| TPM present / FDE | CI (swtpm) / installer | partial/⏳ vTPM boot; FDE deferred (gap #6) |
| Container/K8s workflows, DNS/firewall | — | planned |
| Secret/license/vuln scans, SBOM | CI | ✅ secret scan; ⏳ SBOM (gap #10) |
| Reproducibility across independent builds | CI | ⏳ (gap #2) |
| Accessibility (installer/GUI) | — | planned |

## Failure-injection (§13.3) — coverage map
**Implemented (engine level, `test_failure_injection.py`):** invalid/broken profile config;
required artifact unavailable / invalid signature-checksum (gate refuses); failed resolution
(missing dpkg) → clean error; malformed manifest fuzz; removal/rollback path inputs.

**Still VM-level (require a disposable VM; tracked, not yet automated):**
1. interruption during profile install · 2. disk-full during download/extract/install ·
3. apt/repo unreachable mid-provision · 4. network loss mid-provision · 5. machine reboot during
an operation · 6. package-manager lock contention · 7. DNS resolution failure.
These need a VM harness that pauses/kills/partitions mid-run; planned as a `tests/vm/` suite.

## Environments
- Host/CI unit tests: any Python ≥3.11 (no deps).
- Integration: real Ubuntu 26.04.1 (developer WSL) + in-image during the CI build.
- Images/installer: GitHub Actions runners with `/dev/kvm` (QEMU/OVMF).
- **Never** the developer host or a real disk; **never** real hardware without a named owner.
