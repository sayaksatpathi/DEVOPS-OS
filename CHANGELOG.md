# Changelog

All notable changes to the DevOS project. This project is **pre-Alpha**; entries record Phase 0
planning/audit work, not shipped software.

## Prompt versions governing builds

- **v1.2 — 2026-10-22** — Split Phase 0 into WU-0.1…WU-0.5 (one work unit per session); added
  `docs/upstream-verification.md`, threat-model section, consolidated host/builder requirements,
  26.04.2 HWE note, 26.04.1 date discrepancy note, flavor support-lifetime note,
  timebox→calendar conversion rule. **(Governs current work.)**
- **v1.1 — 2026-10-18** — Pinned baseline to Ubuntu 26.04.1+; Wayland-only planning; Dracut-aware
  recovery; sudo-rs/rust-coreutils compatibility; cgroup v2; TPM/FDE & Landscape/authd decisions;
  CLI privilege/state model; Ansible collection pinning; failure injection; spike timeboxes.

## Project changes

### [Unreleased] — Phase 0

#### 2026-10-22 — WU-0.1: Repository, environment, and upstream audit
- Initialized repository documents: `README.md`, `STATUS.md`, `DECISIONS.md`, `CHANGELOG.md`,
  `docs/upstream-verification.md` (real content; no empty placeholders).
- Audited host/build environment against §16.1 targets; recorded a build-environment blocker
  (insufficient free disk + virtualization firmware disabled + Windows 11 Home).
- Verified Ubuntu 26.04 LTS upstream facts from official release notes (2026-10-22) and logged
  six open discrepancies, including the unpinned exact ISO and a verified Secure Boot risk.
- Recorded baseline decisions (B-01…B-15), WU-0.1 decisions (D-0101…D-0105), and open
  decisions (O-01…O-10).
- No OS built or booted; no ISO downloaded; no VM created.

#### 2026-10-22 — WU-ENG-1: Reproducibility-engine first slice (environment-independent)
- Added provisional profile schema (v0.1.0), the `core` profile, and an illustrative lockfile
  (versions marked PLACEHOLDER/pending — no resolver has run).
- Added the `devos` CLI (`doctor`, `profile list/inspect/validate`, `tools list`, `--version`)
  with documented exit codes; provisioning/apply commands intentionally absent, not stubbed.
- Added a pure-Python, dependency-free validator enforcing schema rules and the §9.1 binary-
  artifact verification policy (no silent trust-on-first-use).
- Added **22 unit tests (all passing)** on Python 3.12.10 (stdlib unittest).
- Flagged a deliberate out-of-phase-order deviation (D-0106) for acknowledgement.
- Still: no OS built or booted; OS-image phases remain blocked on a Linux VM environment.

#### 2026-10-22 — Live-image verification pass (Ubuntu 26.04.1 WSL)
- A developer WSL2 running **Ubuntu 26.04.1 LTS (resolute)** was found; probed read-only.
- Confirmed from the live image: sudo-rs default; **systemd 259** (resolves 258/259 conflict).
- Corrected two assumptions: `cp/mv/rm` are **uutils** here (not GNU) with `coreutils-from-gnu`
  absent; `ID_LIKE=debian` (not `ubuntu debian`). Logged as discrepancies #8/#9.
- Noted WSL limits: MS kernel 6.18, no initrd/UEFI → kernel 7.0, Dracut, boot, Secure Boot,
  TPM/FDE still require a QEMU/OVMF VM. WSL is viable as the engine/Ansible dev sandbox.

#### 2026-10-22 — Ansible provisioning layer for `core` + `devos apply`
- Added `provision/ansible/` (role `devos_core`, `playbooks/core.yml`, `requirements.yml`,
  `ansible.cfg`): idempotent apt install of the core profile's packages; `become` for apt.
- Wired `devos profile apply <name>`: derives the apt list from the profile, **dry-runs with
  `--check` by default**, requires `--confirm` to change the system, `--ask-become-pass` for sudo.
- Added `engine.apt_packages` + pure `cli.build_apply_command`; 6 new unit tests (**28 total, passing**).
- Confirmed `devos doctor` all-ok on the live Ubuntu 26.04.1 WSL.
- Not yet executed: real `apply --confirm` and ansible-lint (ansible-core not installed; user-approved).

#### 2026-10-22 — First real provisioning + lockfile resolution on 26.04.1
- Installed `ansible-core` 2.20.1 from the Ubuntu archive (PyPI was unreachable).
- Ran `devos profile apply core --confirm` on live Ubuntu 26.04.1: Ansible `become` via **sudo-rs**
  (passwordless rule), apt task succeeded, **idempotent (changed=0)** → Alpha-1 criterion #9 met on this env.
- Characterized sudo-rs ↔ Ansible become: interactive password prompt mis-times; passwordless sudo is
  the reliable automation path. Logged in upstream-verification (acceptance #14 datapoint).
- Built `devos profile lock`: resolves installed versions via dpkg-query and writes a schema-valid
  lockfile. Generated a **real** `locks/core.lock.json` (5/5 resolved) from the live image.
- Added `engine.parse_dpkg_query` + pure `cli.build_lockfile`; 6 new tests (**35 total, passing**).

#### 2026-10-22 — Open-sourced and published to GitHub
- Added Apache-2.0 LICENSE (provisional), CONTRIBUTING, CODE_OF_CONDUCT, SECURITY,
  .gitignore, .gitattributes (LF enforcement), issue/PR templates.
- Added CI (`.github/workflows/ci.yml`): unit tests (3.11/3.12), profile validation,
  gitleaks secret scan, ansible-lint (advisory).
- Added `docs/build-and-release.md` (full-OS image architecture: packages baked into the ISO
  or applied at first boot via the same devos/Ansible engine), guarded `image/build.sh`
  skeleton, and `services/devos-firstboot/` scaffold.
- Published source to github.com/sayaksatpathi/DEVOPS-OS (main). No built/signed images.

#### 2026-10-22 — Engine completion: lifecycle commands, containers profile, verify module
- Refactored Ansible to a generic `devos_apt` role + `playbooks/apply.yml` (install/remove via
  a `state` var; never autoremove/purge on removal → preserves user data).
- Added commands: `profile remove` (dry-run default), `drift check`, `update` (read-only sim).
  Verified on live 26.04.1: generic apply idempotent (changed=0); drift shows no drift; update
  detected a real curl security update (…2.7 → …2.8).
- Added `containers` profile (rootless Podman + userspace net/storage tools).
- Added `verify.py`: SHA-256 integrity + §9.1 install policy (signature/attestation/approved
  fallback; rejects trust-on-first-use). apply now skips binary tools and says so (pending
  verified-download wiring).
- Tests 35 → **48, all passing**.

#### 2026-10-22 — 🟢 First bootable DevOS image built in CI
- GitHub Actions run 39751210254 (green): built a bootable DevOS **cloud image** (qcow2, ~1.28 GB)
  from the official Ubuntu 26.04.1 cloud image.
- Provisioned by booting the image in QEMU (KVM) and running `devos profile apply core,containers`
  inside it (DEVOS_PROVISION_OK), then virt-sysprep hygiene.
- Boot-tested under UEFI/OVMF: "BOOT TEST PASSED: image boots under UEFI and core profile tools
  are present."
- CI fixes to get here: removed passt (libguestfs net), appliance networking unusable → redesigned
  to provision-by-booting, fixed QEMU -accel flag.
- Still: server/cloud flavor only (desktop ISO future); experimental, unsigned; artifact expires 7 days.

#### 2026-10-22 — Verified binary-tool install + infra profile; downloadable release
- Added `infra` profile: OpenTofu v1.13.2 installed from a verified upstream binary
  (checksum pinned from OpenTofu's signed SHA256SUMS).
- Wired binary-tool install into `apply`: the §9.1 policy gate (verify.py) runs first and
  refuses trust-on-first-use; allowed tools install via a new `devos_binary` Ansible role
  (get_url with checksum verification → /usr/local/bin). Dry-run reports intent; --confirm installs.
- Tests 48 → **52, all passing**; verified on real WSL (gate passes OpenTofu, playbook wires up).
- Added release step: on a `v*` tag, CI attaches the bootable qcow2 to a GitHub prerelease.
- Cut tag v0.1.0-alpha1 to publish the first downloadable DevOS image.

#### 2026-10-22 — Signing/provenance, trademark docs, desktop profile
- Release pipeline now signs images keyless (Sigstore/cosign sign-blob), attaches a build
  manifest, and emits a SLSA build-provenance attestation (no production key custody).
- Added docs/licensing-and-trademarks.md: trademark status (provisional, NOT cleared), the
  clearance steps to run, and image-redistribution license obligations.
- Added `desktop` profile (GNOME: ubuntu-desktop-minimal + gdm3) and a manual desktop-image
  build job (workflow_dispatch desktop=yes) producing a bootable GNOME desktop qcow2.
- Local footprint cleanup (git gc); project uses ~223 KB — D: usage is unrelated user data.

#### 2026-10-22 — Failure-injection tests + subsystem register + threat model
- Added engine-level failure-injection suite (Alpha-1 #18 testable subset): bad/malformed
  profiles, supply-chain fail-closed, missing prereqs, and 1000-iteration validator fuzzing.
  Tests 52 -> 62, all passing. VM-level injection cases tracked in testing-strategy.
- Added docs/subsystem-register.md (WU-0.2) — every §6 subsystem with honest status.
- Added docs/threat-model.md (WU-0.3) — §11.0 threat categories with mitigations/evidence/residual.

#### 2026-10-22 — Close completable gaps: rollback, system-update, CI verifications, backbone docs
- Engine: `devos profile rollback` (pin exact versions from a lockfile) and `devos update --system`
  (whole-OS update preview). 63 tests passing.
- CI verifications added: Secure Boot boot test (signed chain under SB), vTPM boot test, in-image
  idempotency assertion (second apply changed=0), package SBOM (CycloneDX on release), desktop GNOME
  session assertion (gdm3 enabled + gnome-shell).
- Docs: ADR set (docs/adr), governance.md, hardware-compatibility.md, recovery-backup-rollback.md,
  package-and-update-lifecycle.md, testing-strategy.md; licensing/trademarks updated (informal name
  search, archive-component allowlist).

#### 2026-10-22 — Production-hardening: CVE/license scan, reproducibility, VM failure injection
- CI: Trivy CVE scan (HIGH/CRITICAL) + license scan of the image, reports attached to releases (gaps #6/#7).
- CI: independent-reproducibility job — builds the image twice and asserts identical package sets (gap #14/#8).
- CI: VM-level failure-injection suite (tests/vm/failure-injection.sh) — missing artifact, bad checksum,
  dpkg-lock contention, malformed profile; asserts clean non-zero failure (gap #13).

#### 2026-10-22 — Close the 5 automatable production gaps
- #1 installer install->reboot->login: boot-installer-test now boots the INSTALLED disk and
  asserts it reaches a login prompt.
- #2 FDE: LUKS-encrypted installer variant (image/autoinstall/user-data-fde; build FDE=1).
- #3 recovery: restic backup->restore test (tests/vm/backup-restore.sh) in the failtest job.
- #4 OS upgrade: upgrade-test.sh applies apt full-upgrade in-guest and verifies reboot->login.
- #5 CVE: reliable Trivy scan of the generated CycloneDX SBOM (no flaky qcow2 mount); SBOM now
  generated on every build and attached to releases.

#### 2026-10-23 — Fix critical holes from the OS-researcher audit
- Hole #1 lockfile enforcement: `apply` installs pinned name=version from the lockfile when present.
- Hole #2 REAL signature verification: devos_binary cosign-verifies upstream SHA256SUMS against the
  project release identity, derives the checksum from the VERIFIED sums; gate now rejects a bare
  "upstream-signature" label lacking sig material (was TOFU).
- Holes #4/#5 hardening+telemetry: devos_hardening role (UFW default-deny+OpenSSH, sysctl hardening,
  SSH key-only/no-root, apport/whoopsie masked, motd-news/apt-news/ubuntu-report off) applied to
  every image and in the installer.
- Hole #3 installer: SSH password auth disabled (key-only), installed account password expired.
- Hole #7 containers: real `podman run` smoke test during provisioning.
- Hole #8 SBOM completeness: binary tools (OpenTofu) + the devos engine now included in the SBOM.
- 64 unit tests pass. (Holes #6 SB-chain, #9 desktop-render, #10 FDE-unlock remain partial.)

#### 2026-10-23 — OS-upgrade test green (gap #4 closed)
- Verified: in-guest `apt full-upgrade` applies and the system converges (DEVOS_UPGRADE_OK).
- Fixes along the way: hold cloud-init/snapd (self-disruption), NEEDRESTART_MODE=a +
  --force-confold (no prompts), judge success by convergence state not the noisy exit code.

#### 2026-10-23 — Secure Boot enforcement verified in-guest (hole #6 closed)
- SB boot test now requires DEVOS_SECUREBOOT_ENFORCED — emitted only when `mokutil --sb-state`
  reports "SecureBoot enabled" inside the booted guest. Upgrades #6 from "boots under secboot
  firmware" to "SB enforcing with a signed kernel, confirmed in-guest". Verified green.

#### 2026-10-23 — Desktop render verified (#9) + image-hygiene verification (§11)
- #9 CLOSED: desktop image boots and gnome-shell greeter actually runs on a virtio GPU
  (DEVOS_DESKTOP_RENDER_OK) — real render proof, not just binary presence.
- §11 image-hygiene VERIFICATION (was only asserted): image/verify-hygiene.sh scans the built
  qcow2 offline and FAILS the build on any leak — machine-id, SSH host keys, bash history,
  builder source tarball, or root authorized_keys. Also removes /opt/devos-src.tar.gz.

#### 2026-10-23 — §11 build integrity, §12 QA, §2 auditd
- §11: SOURCE_DATE_EPOCH from the source commit (reproducible timestamps).
- §12: compressed-image-size performance budget (enforced); ansible-lint now ENFORCED
  (was advisory) with a .ansible-lint policy.
- §2: auditd installed + enabled in the hardening role.

#### 2026-10-23 — §10 installer completeness + §2 pin Actions by SHA
- §10: installer now sets timezone, applies security updates during install, configures
  networking explicitly with IPv6 (dhcp6).
- §2 supply chain: all GitHub Actions pinned to full commit SHAs (tag-movement attacks).

#### 2026-10-23 — #10 FDE unlock test (last critical hole)
- Installed-system boot for an FDE install injects the LUKS passphrase over a bidirectional
  serial pipe and asserts the encrypted disk unlocks and reaches login (FDE UNLOCK PASSED).

#### 2026-10-23 — §5 corporate-CA trust
- devos_ca role: system CA bundle made authoritative for Node/Python/curl/git/Rust via
  /etc/profile.d; installs admin-provided CA certs. Applied to every image.

#### 2026-10-23 — §1 Kubernetes profile + §8 snapshot reproducibility
- §1: `kubernetes` profile (kubectl) via cosign blob verification; new blob-verify mode.
- §8: DEVOS_APT_SNAPSHOT build option pins apt to snapshot.ubuntu.com (deb822 Snapshot) for
  strict, time-stable reproducibility. Default is a no-op.

#### 2026-10-23 — §4 SSD TRIM + §3 GRUB defaults
- §4: enable fstrim.timer (periodic SSD TRIM) in baseline.
- §3: GRUB defaults drop-in (visible menu, recovery entries kept) + update-grub.
