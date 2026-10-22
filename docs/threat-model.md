# Threat Model

Master-prompt §11.0. For each threat: asset · attacker · trust boundary crossed · mitigation ·
evidence/test · residual risk. Reviewed at every phase exit and when a new privileged capability,
network service, or external dependency is proposed. Status is honest; "planned" means no
mitigation is implemented yet. Last updated 2026-10-22 (WU-0.3).

> **Scope note:** DevOS today ships *no* privileged helper, root daemon, remote API, or telemetry
> endpoint. `devos` runs unprivileged; elevation is per-operation via sudo. This keeps the current
> attack surface small, which is why several rows below are "not applicable yet."

## T1 — Malicious/compromised packages, repos, or upstream binaries
- **Asset:** the built image and installed systems. **Attacker:** a poisoned apt mirror or a tampered binary download.
- **Mitigation:** apt signature chain (inherited); base image checksum + **GPG** verified; binary tools gated by `verify.py` (signature/attestation + checksum, **TOFU refused**) and `get_url` re-checks the checksum.
- **Evidence:** CI build log shows "SHA256SUMS GPG signature: OK"; `test_verify.py`, `test_binary.py`, `test_failure_injection.py`.
- **Residual:** no per-package SBOM/CVE scan of the shipped image yet (gap #10); binary signature *chain* (GPG/cosign of SHA256SUMS) is pinned-by-checksum, not re-verified at install.

## T2 — Tampered profile manifests, lockfiles, Ansible roles
- **Asset:** privileged provisioning (profiles drive apt/become). **Attacker:** a malicious PR or edited profile.
- **Mitigation:** strict schema validation (rejects unknown fields, bad sources); validators **fuzz-tested to never crash**; lockfiles require pinned versions; CI runs validation + tests on every PR; roles are in-repo and reviewed.
- **Evidence:** `test_schema.py`, `test_failure_injection.py` (1000-iteration fuzz), CI.
- **Residual:** no signing of profiles themselves; a trusted committer is assumed.

## T3 — Compromised build deps, base image, builder/CI runner
- **Asset:** release artifacts. **Attacker:** a hijacked Action or base input.
- **Mitigation:** pinned base image (verified), build runs on GitHub-hosted runners, **keyless Sigstore signing + SLSA build-provenance attestation** bind artifacts to the exact workflow run.
- **Evidence:** signed v0.1.0-alpha2 release (.sig/.pem + attestation).
- **Residual:** third-party Actions pinned by major tag, not SHA; no isolated builder separation of PR vs trusted build beyond GitHub's.

## T4 — Local privilege escalation (devos, sudo-rs, group membership, helpers)
- **Asset:** root on the installed system. **Attacker:** a local user or a malicious profile.
- **Mitigation:** `devos` unprivileged by default, no setuid binary, no root daemon; `docker`-group root-equivalence documented and not granted silently; passwordless sudo is a *dev-sandbox* convenience, **not** the shipped model.
- **Residual:** the installer's dev account + forced password change is coarse; a narrow per-operation elevation model (polkit) for any future GUI is unbuilt.

## T5 — Insecure container privileges / rootless escape / weakened confinement
- **Mitigation:** containers profile targets **rootless Podman**; AppArmor/userns left at Ubuntu defaults (not weakened).
- **Status:** **planned** — rootless workflow and confinement not load-tested; no evidence yet.

## T6 — Stolen SSH/GPG keys, cloud tokens, kubeconfigs, Terraform state
- **Mitigation:** no secrets bundled in images; `.gitignore` + CI secret scan (gitleaks); image hygiene clears builder creds.
- **Evidence:** secret scan job; repo secret probe clean.
- **Residual:** no secrets-management workflow (SOPS/age) shipped; kubeconfig/TF-state guidance unwritten.

## T7 — Firmware, bootloader, Secure Boot, TPM, initramfs tampering
- **Status:** **blocked** — Secure Boot not verified end-to-end (gap #5); TPM/FDE unimplemented (gap #6). Known upstream risk: unsigned intel-ipu7 modules break Secure Boot.

## T8 — Unauthenticated/downgraded/rolled-back updates, metadata replay
- **Mitigation:** apt metadata expiry (inherited). **Status:** DevOS-level update/rollback story **not addressed** (gap #9).

## T9 — Secrets in images, logs, diagnostic bundles, CI artifacts
- **Mitigation:** virt-sysprep strips logs/history/identity; CI secret scan; `devos` logs aim to be secret-safe.
- **Residual:** no diagnostic-bundle redaction implemented; not audited.

## T10 — Destructive install/provisioning (data loss)
- **Mitigation:** all build/install/boot tests run **only in disposable VMs** against blank disks; `profile remove` never autoremoves/purges (preserves user data).
- **Evidence:** CI uses throwaway target disks; `test_apply.py` state tests.
- **Residual:** the installer uses a `direct` whole-disk layout (wipes target) — correct for unattended VM install, dangerous on real hardware; no "are you sure" on bare metal.

## T11 — Hostile networks / DNS tampering / corporate CA & proxy misuse
- **Status:** **planned** — split-DNS, VPN MTU, corporate-CA trust stores documented as risks, not mitigated or tested.

## T12 — Malicious GUI apps / Wayland capture / exposed services
- **Status:** **planned** — desktop confinement and screen-capture portals not assessed.

## T13 — Release-signing-key compromise
- **Mitigation:** **no long-lived signing key exists** (keyless Sigstore) — nothing to steal. A future production key would need HSM custody, rotation, revocation (DECISIONS O-pending).

## Review gate
No privileged helper, root daemon, remote API, telemetry endpoint, or auto-exposed network
service may ship before the relevant row above is implemented, tested, and re-reviewed.
