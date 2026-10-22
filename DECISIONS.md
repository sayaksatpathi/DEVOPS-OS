# DECISIONS

Running log of baseline product decisions and open decisions. Material choices get a full ADR
under `docs/adr/` (created in WU-0.4). Until then, this file is the single decision log.
**Last updated:** 2026-10-22 (WU-0.1).

## Contributor availability (for §16.1 timebox → calendar conversion)

**Not yet provided by the user.** Timeboxes in the master prompt are **working days of focused
effort**; calendar duration depends on weekly availability. This must be recorded before any
spike is scheduled. **Placeholder: UNKNOWN.** (Action: capture in a future session.)

## A. Baseline product decisions (accepted unless superseded)

These mirror master-prompt §2 and are treated as the initial baseline. Any change requires an
entry here + `STATUS.md` + `CHANGELOG.md` and approval if it alters a core decision.

| ID | Decision | Status |
|----|----------|--------|
| B-01 | Product type: DevOps-specialized workstation OS | accepted (baseline) |
| B-02 | Foundation: Ubuntu **26.04.1+** Desktop (pin exact artifact at build time) | accepted (baseline) |
| B-03 | Architecture: x86-64/AMD64; Intel & AMD; no micro-arch-only target | accepted (baseline) |
| B-04 | Targets: laptops, desktops, suitable VMs | accepted (baseline) |
| B-05 | Experience: CLI + full GNOME desktop | accepted (baseline) |
| B-06 | Desktop: reuse Ubuntu GNOME 50 **Wayland-only** session | accepted (confirmed upstream) |
| B-07 | Provisioning: Ansible + Ubuntu package mgmt + verified installers | accepted (baseline) |
| B-08 | Kernel: Ubuntu **generic** kernel 7.0 (no custom kernel in v1) | accepted (baseline) |
| B-09 | Snap: retained for Alpha-1 | accepted (baseline) |
| B-10 | Secure Boot: use Ubuntu-signed shim/GRUB/kernel unmodified | accepted (baseline) |
| B-11 | Build/test isolation: disposable builder VM + QEMU/OVMF only; never the host/real disk | accepted (baseline, enforced) |
| B-12 | Initial release: local experimental Alpha-1; no public release | accepted (baseline) |
| B-13 | Name `DevOS` provisional until trademark/domain/branding review | accepted (baseline) |
| B-14 | CLI name `devos`, unprivileged by default; per-op elevation only | accepted (baseline) |
| B-15 | v1 is UEFI-only; no legacy BIOS/CSM; no 32-bit; no Apple T2; no RAID promise | accepted (baseline) |

## B. Decisions made in WU-0.1

| ID | Decision | Rationale |
|----|----------|-----------|
| D-0101 | Scope this session to **WU-0.1 only**, then stop | Safety rule §16 (one scoped work unit per session) |
| D-0102 | Do **not** create empty placeholder docs/dirs for later WUs | §20 forbids reporting empty files as complete |
| D-0103 | Treat all upstream facts as "confirmed from release notes," **not** from a pinned image | No image inspected yet; §5.2/§7.6 require artifact inspection |
| D-0104 | Record the host as **incapable of running the mandated builder/test VMs as configured** | 45.5 GB free disk + virtualization firmware disabled + Win 11 Home (no Hyper-V); §16.1 forbids starting a build with inadequate capacity |
| D-0105 | Flavor 3-year support lifetime marked **unverified** | Official release-cycle page gives no flavor duration; prompt figure not corroborated |
| D-0106 | Build the **reproducibility-engine slice early** (out of strict phase order), because it is environment-independent and OS-image phases are blocked | Delivers the core value prop now; no VM needed; honest status markers keep it from masquerading as a booted OS. **Deviation from §17 phase order — flagged for acknowledgement.** |
| D-0107 | Engine profile/lock format is **JSON** in this slice; validator & tests are **stdlib-only** (no pyyaml/jsonschema/pytest) | Must run dependency-free inside a minimal builder VM with no network |
| D-0108 | Project licensed **Apache-2.0** (provisional) for DevOS's own code/docs | User chose open source so others can build/upgrade; Apache-2.0 adds a patent grant + is contributor-friendly. Distributed **images** still carry upstream licenses; full §7.1 review and `DevOS`/`DEVOPS-OS` trademark clearance still required before public release |
| D-0109 | Full-OS delivery = Ubuntu 26.04.1 **derivative** with profiles baked in at build time (Path A) or first boot (Path B), using the same `devos`/Ansible engine | Reuses mature Ubuntu boot/installer/desktop; the reproducibility engine is the baking mechanism. ISO build **blocked** pending a Linux builder VM |
| D-0110 | Publish source to **github.com/sayaksatpathi/DEVOPS-OS** | User explicitly authorized the push; source only (no signed images, no secrets) |

## C. Open decisions (owner / resolve in later WUs)

| ID | Open decision | Target WU |
|----|---------------|-----------|
| O-01 | **Build/test environment path**: enable virt + free disk for local WSL2/QEMU, vs external/isolated Linux builder, vs approved cloud runner. Host remediation needs user approval. | next (ADR) |
| O-02 | Image-building route: custom Desktop ISO (10-day spike) vs documented bootstrap fallback | WU-0.4 |
| O-03 | Exact base ISO pin: URL + SHA256 + GPG signature + arch + build date | build phase |
| O-04 | Ubuntu archive-component allowlist (main/restricted/universe/multiverse) + per-dep license review | WU-0.3 |
| O-05 | Project license + DCO/CLA | WU-0.3 / §14 |
| O-06 | Container runtime (rootless Podman vs rootless Docker) + firewall model | WU-0.2/§9 |
| O-07 | Filesystem/encryption/swap/backup model (ext4 baseline; TPM/FDE use/offer/defer) | WU-0.4 (ADR 15) |
| O-08 | Landscape & authd: use / optional-install / defer | WU-0.4 (ADR 16) |
| O-09 | Remote desktop: GNOME Remote Desktop + PipeWire vs xRDP (Wayland) | WU-0.4 (ADR 17) |
| O-10 | Support-end month (April vs May 2031) reconciliation before any support promise | §14 |
| O-11 | Adopt a YAML loader for profiles/lockfiles (vs keep JSON) | WU-0.4 / Phase 3 |
| O-12 | Ansible layer: `requirements.yml` + reviewed `locks/ansible-collections.lock.yaml` | Phase 3 |

## D. Change-control note

This file, `STATUS.md`, and `CHANGELOG.md` must be updated at the end of every session.
Substantive changes to baseline decisions (section A) require explicit approval.
