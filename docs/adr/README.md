# Architecture Decision Records

Material decisions (master-prompt §16). Each: ID · status · context · decision · consequences ·
revisit. Status: accepted · proposed · blocked · deferred. Last updated 2026-10-22 (WU-0.4).

---
## ADR-0001 — Ubuntu 26.04.x LTS base & support lifecycle · **accepted**
**Context:** need a maintained, UEFI/Secure-Boot-capable desktop base. **Decision:** build on the
official Ubuntu 26.04.1+ server/cloud image (derivative, not a fork); reuse kernel/boot/installer/
desktop. **Consequences:** inherit 5-yr maintenance; carry Ubuntu identity + obligations. **Revisit:**
if 26.04 proves unsuitable (evidence in upstream-verification.md).

## ADR-0002 — Image build method: cloud-image + autoinstall, not hand-rolled live ISO · **accepted**
**Context:** the dev host can't build ISOs; appliance networking is broken on CI. **Decision:**
provision by *booting* the official cloud image in QEMU (networking works), and build an installer
via Ubuntu **autoinstall** on the live-server ISO. **Consequences:** reproducible in CI, no custom
live-build maintenance; a bespoke GNOME live ISO remains out of scope. **Revisit:** if a desktop
live ISO becomes a requirement.

## ADR-0003 — Snap retained for Alpha-1 · **accepted**
Keep Ubuntu's Snap integration; removing it risks breaking Store/Firefox/installer. Revisit per
an explicit, tested decision.

## ADR-0004 — Secure Boot: reuse Ubuntu-signed chain, no custom trust · **accepted (SB test blocked)**
**Decision:** use Ubuntu's signed shim/GRUB/kernel unmodified; do not build a custom trust chain.
**Consequences:** DKMS/unsigned modules (e.g. intel-ipu7) can break SB — tracked. End-to-end SB
verification is a CI test (secure-boot OVMF) being added; not yet green. **Revisit:** if a signed
custom chain is ever needed (requires key custody + review).

## ADR-0005 — Kernel: generic 7.0, HWE deferred · **accepted**
Use the generic kernel; no HWE stack until 26.04.2. cgroup v2 only. Revisit at 26.04.2.

## ADR-0006 — Filesystem ext4; TPM/FDE deferred; no atomic rollback claim · **deferred (FDE)**
**Decision:** ext4 baseline; **defer** TPM-backed full-disk encryption for Alpha-1 (installer
supports it, but Secure-Boot/DKMS/recovery-key interactions are untested). Rollback is
**profile/tool-level only** (`devos profile rollback`), never atomic system rollback on ext4.
**Revisit:** evaluate Btrfs/Snapper + TPM/FDE with a recovery analysis before any stable release.

## ADR-0007 — Container runtime: rootless Podman; firewall default · **accepted**
Rootless Podman default (no `docker` group root-equivalence granted silently). UFW/nftables model
documented; don't disable the firewall for containers. Revisit if rootless Docker is required.

## ADR-0008 — Profile/lockfile format JSON; toolchain ownership · **accepted**
JSON profiles/lockfiles, stdlib-only validator (runs dependency-free in a builder). `/usr/local/bin`
for verified binaries; `devos` owns system tools, user owns personal dotfiles. Revisit YAML (O-11).

## ADR-0009 — CLI privilege & state model · **accepted**
`devos` unprivileged by default; per-op sudo elevation; no setuid, no root daemon. State under
`/etc/devos`, `/var/lib/devos`, `~/.config/devos` etc. A future GUI needs a reviewed polkit action
before shipping (threat-model gate).

## ADR-0010 — Telemetry off; Pro/Livepatch/ESM opt-in · **accepted**
DevOS telemetry defaults **off**; no automatic diagnostic upload. Ubuntu Pro/Livepatch/ESM only if
the user enables them. An opt-in hw-probe report requires a reviewed privacy model first.

## ADR-0011 — Release signing: keyless Sigstore, no production key custody · **accepted**
**Decision:** sign releases with keyless Sigstore (cosign sign-blob via OIDC) + SLSA build-provenance
attestation; **do not** generate a long-lived production signing key. **Consequences:** verifiable
provenance with nothing to steal; offline-without-Sigstore verification unavailable. **Revisit:** if
an air-gapped verification path is needed (then HSM-backed key + custody plan).

## ADR-0012 — License & branding: Apache-2.0 code; `DevOS` provisional · **accepted (name provisional)**
Apache-2.0 for DevOS code/docs; images carry upstream licenses. Name `DevOS`/`DEVOPS-OS` is
**provisional**; no registered OS trademark found but a formal clearance + possibly a more
distinctive name is required before public branding (see licensing-and-trademarks.md).

## ADR-0013 — Versioning & EOL: CalVer-ish alpha tags; support tied to Ubuntu · **proposed**
`v0.x.y-alphaN` now; support window tracks the Ubuntu base. Stable governance (SLA/EOL) defined in
docs/governance.md before any stable release. Revisit at first beta.

## ADR-0014…0019
Covered inline in upstream-verification.md (Wayland/Dracut/sudo-rs/coreutils/cgroup), the
subsystem-register, and licensing-and-trademarks.md (archive components, Landscape/authd, remote
desktop). Promote to standalone ADRs as those areas are implemented.
