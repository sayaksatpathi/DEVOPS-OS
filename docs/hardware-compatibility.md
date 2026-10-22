# Hardware Compatibility

Master-prompt §6.3/§13 (gap #8). **Honest status: ZERO physical hardware has been tested.**
Everything to date is VM-only (QEMU/OVMF). VM results are **not** evidence for battery, thermal,
Wi-Fi chipset, suspend/resume, or GPU behavior. This file is the matrix + the plan; it will stay
mostly empty until someone runs DevOS on real machines.

## Compatibility classes
- **VM-tested** — boots/installs under QEMU/OVMF (what we have).
- **Architecture-compatible** — x86-64; expected to work by Ubuntu driver support, unverified.
- **Physically tested** — a named owner ran it on real hardware (none yet).
- **Known limitation / Unsupported** — recorded exceptions.

## Matrix (to be filled by testers)
| Owner | Model / chipset | Firmware | Kernel | GPU/driver | Secure Boot | Suspend/resume | Wi-Fi | Battery | Date | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| — | QEMU q35 + OVMF | OVMF | 7.0 (cloud) | virtio | not-yet | n/a (VM) | n/a | n/a | 2026-10-22 | boots/installs ✅ |
| _you_ | _add a row_ | | | | | | | | | |

## v1 unsupported (stated plainly)
Legacy BIOS/CSM · 32-bit CPUs · Apple T2 · RAID (unless separately validated) · any
"universal hardware compatibility" claim.

## How to contribute a hardware test (the only way #8 gets closed)
1. Install a DevOS image in a **disposable** setup (spare disk / external SSD), never your only machine.
2. Record: model, firmware, `uname -r`, GPU + driver, `mokutil --sb-state`, suspend/resume result,
   Wi-Fi chipset (`lspci -nnk`), battery reporting.
3. Open a PR adding a matrix row (or an issue with the details). Redact serials/identifiers.

## Opt-in hardware report (planned, privacy-gated)
A future `devos hw-report` would collect the above **locally**, show you exactly what it gathered,
let you review before sharing, redact personal data, and never transmit automatically. It is NOT
implemented — it requires the privacy model in ADR-0010 to be reviewed first.
