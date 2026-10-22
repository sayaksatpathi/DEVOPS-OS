# STATUS

**Last updated:** 2026-10-22
**Prompt version governing this work:** v1.2 (2026-10-22)
**Work units completed:** WU-0.1 (audit) + WU-ENG-1 (reproducibility-engine first slice)
**Phase:** 0 complete for WU-0.1; a Phase 3/4 slice built early because it is
environment-independent (see decision D-0106). OS-image phases (1,2,5) remain **blocked**.

---

## 1. What already exists / what is missing

**Repository starting state:** `D:\OS` was **empty** and **not a git repository**. No prior
source, specs, scripts, tests, or licenses existed.

**Created this session (real content, WU-0.1 scope only):**

| File | Status | Notes |
|------|--------|-------|
| `README.md` | implemented | Project overview, phase, safety summary |
| `STATUS.md` | implemented | This file |
| `DECISIONS.md` | implemented | Baseline product decisions + open decisions |
| `CHANGELOG.md` | implemented | Prompt-version + work-unit log |
| `docs/upstream-verification.md` | implemented | Verified facts, discrepancies, re-verify checklist |

**Deliberately NOT created** (later work units; empty placeholders are forbidden by §20):
subsystem register (WU-0.2), threat model / licensing / privacy inventory (WU-0.3), ADR set &
image-method spike (WU-0.4), roadmap + Alpha-1 test plan + PoC selection (WU-0.5), and all of
`image/ installer/ system-config/ boot/ packages/ services/ desktop/ profiles/ locks/
provision/ recovery/ tests/ scripts/ licenses/ .github/`. These are **planned**.

**🟢 BOOTABLE IMAGE ACHIEVED (2026-10-22).** GitHub Actions run 39751210254 built a real
DevOS **cloud image** (qcow2, ~1.28 GB) from the official Ubuntu 26.04.1 cloud image, baked in
the `core`+`containers` profiles by booting the image and running `devos profile apply` inside
it (`DEVOS_PROVISION_OK`), ran image hygiene, and **boot-tested it under UEFI/OVMF**
(`BOOT TEST PASSED: image boots under UEFI and core profile tools are present`). Downloadable
artifact: `devos-cloud-image`. This is a server/cloud flavor; a desktop ISO reuses the same
pipeline and is still future. Not a signed public release.
**Alpha-1 criteria now demonstrated in CI:** #1 (clean QEMU/OVMF VM boots the produced image),
#2 (reaches a usable session), #4 (pinned base verified by checksum + GPG), partial #5
(machine-id/SSH-host-key reset via virt-sysprep).

**Reproducibility engine — first vertical slice (WU-ENG-1), real + tested:**

| Path | Status | Notes |
|------|--------|-------|
| `profiles/schemas/profile.schema.json` | implemented | Provisional v0.1.0 contract (JSON) |
| `profiles/definitions/core.json` | implemented | Core profile (git, openssh-client, curl, jq, ca-certificates) |
| `profiles/definitions/containers.json` | implemented | Rootless Podman profile (podman, uidmap, slirp4netns, passt, fuse-overlayfs) |
| `locks/core.lock.json` | implemented (real) | **5/5 resolved** from live 26.04.1 via `devos profile lock` (e.g. git `1:2.53.0-1ubuntu1`); baseImage digest still UNVERIFIED (no pinned ISO) |
| `packages/cli/devos/` | implemented | `doctor`, `profile list/inspect/validate/apply/remove/lock`, `drift check`, `update`, `tools list`, `--version` |
| `packages/cli/devos/verify.py` | implemented | §9.1 supply-chain gate: sha256 verify + install policy (sig/attestation/approved-fallback) |
| generic Ansible role `devos_apt` + `playbooks/apply.yml` | implemented | Shared install/remove role used by every profile |
| `provision/ansible/` (role `devos_core`, playbook, requirements.yml, cfg) | implemented | Core profile → idempotent apt install; collections empty (core = ansible.builtin only) |
| `devos profile apply` | implemented (dry-run-safe) | Derives apt list from the profile; **`--check` by default**, real changes need `--confirm` |
| `tests/unit/` (schema, cli, apply, lock, verify) | tested | **48 tests, all passing** |

**Proven on real Ubuntu 26.04.1 (WSL), end to end:** `devos doctor` all-ok → `profile validate`
→ `profile apply core --confirm` (Ansible + **sudo-rs** become, **idempotent: changed=0** on
re-run → Alpha-1 criterion #9) → `profile lock core` (**real** versions resolved) → `tools list`.
`ansible-core` = 2.20.1 (from apt).
**Alpha-1 criteria touched:** #9 (idempotence) ✅ on this env; #14 (sudo-rs/coreutils compat) —
sudo-rs `become` characterized (needs passwordless sudo; interactive prompt mis-times) ✅.
**Not yet done:** `ansible-lint`/Molecule; narrow (non-NOPASSWD) elevation model; pinned-ISO digest.

**Still planned** (honest gaps, not stubbed): `profile upgrade` (version-bump preview);
`ansible-lint`/Molecule hardening; signature-chain (GPG/cosign) verification at install time
(engine pins checksums from signed SHA256SUMS and enforces the policy gate today).

Run it: `PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python -m devos profile validate --all`
Test it: `PYTHONPATH=packages/cli python -m unittest discover -s tests/unit`

**No OS has been built or booted.** No ISO downloaded, mounted, or inspected. No VM created.

## 2. Host & builder capacity vs. §16.1 planning targets

| Metric | This host | §16.1 min / recommended | Verdict |
|--------|-----------|-------------------------|---------|
| CPU threads | 16 | 4 / 8+ | ✅ meets recommended |
| RAM | ~15.6 GB | 8 GB / 16–32 GB | ⚠️ meets min; low edge of recommended |
| Free disk (D:) | 45.5 GB | — / 60–80 GB VM, 150 GB recommended | ❌ **below** builder/test-VM target |
| Virtualization firmware | reports **disabled** | required (nested-virt for VMs) | ❌ **blocking** as configured |
| OS | Windows 11 **Home** Single Language | Linux builder expected | ⚠️ no Hyper-V on Home; WSL2 present |

**Host finding:** This is a **Windows 11 Home** machine. The spec mandates image construction
and boot/install tests inside **disposable Linux builder/test VMs** (QEMU + OVMF, optional
swtpm). As currently configured this host **cannot** run them, for two independent reasons:
(a) only **45.5 GB** free disk vs. a 60–80 GB per-VM target; (b) CPU virtualization reports
**disabled in firmware**, which blocks WSL2/QEMU/KVM/Hyper-V. Windows 11 Home also lacks
Hyper-V. Per safety rule §16.1, a long-running/destructive build must **not** begin with
inadequate capacity. `wsl.exe` is present, so WSL2 becomes viable **only after** virtualization
is enabled in BIOS/UEFI and disk is freed.

## 3. Upstream verification summary

Full detail in [`docs/upstream-verification.md`](docs/upstream-verification.md). Headlines,
all **confirmed from official Ubuntu release notes on 2026-10-22** (not yet from a pinned image):
GNOME 50; Ubuntu Desktop session **Wayland-only**; **sudo-rs** default (C sudo → `sudo.ws`);
**rust-coreutils** core provider (but `cp/mv/rm` stay GNU; GNU restorable); **Dracut** default
initrd (initramfs-tools still switchable); **cgroup v1 removed**; TPM/FDE improved (no
re-encryption; Nvidia-only out-of-tree); kernel **7.0**; 5-yr support (10-yr ESM/Pro).

**Open discrepancies (not resolved in WU-0.1):** support-end month April vs May 2031; systemd
258 vs 259 for cgroup removal (same page); flavor 3-yr lifetime **unverified**; 26.04.1 exact
date secondary-sourced; **exact ISO artifact not yet pinned**; verified Secure Boot risk
(unsigned `intel-ipu7` modules break Secure Boot).

## 4. Highest-risk unresolved decisions

1. **Build/test environment.** No capable disposable-VM environment exists on this host.
   Must choose a path (enable virt + free disk for WSL2/QEMU locally; external Linux builder;
   or an approved isolated runner/cloud). Remediation on the host needs user approval.
2. **Image-building route.** Custom Ubuntu **Desktop** ISO construction is unproven; the §16.1
   ISO spike is timeboxed to 10 working days with a documented bootstrap-route fallback. Not started.
3. **Exact base-image pinning** (URL + checksum + signature). Open; required for Alpha-1.
4. **Legal/trademark/licensing** — `DevOS` name provisional; archive-component allowlist and
   per-dependency license review not started (WU-0.3).
5. **Secure Boot + DKMS + TPM/FDE interactions**, informed by the verified unsigned-module risk.

## 5. What cannot be tested in this environment

- Any OS boot/install, QEMU/OVMF boot, Secure Boot, TPM/FDE, failure-injection — **blocked** by
  §2 (no capable VM environment).
- Any physical-hardware behavior (battery, thermal, Wi-Fi chipset, suspend/resume, firmware) —
  requires separately approved physical test hardware; VM results never substitute.

## 6. Commands run this session (for reproducibility)

```
pwd; ls -la D:/OS                 # empty dir
git rev-parse --is-inside-work-tree   # fatal: not a git repository
nproc                             # 16
Get-CimInstance Win32_ComputerSystem .TotalPhysicalMemory  # ~16013 MB
(Get-PSDrive D).Free              # 45.5 GB
where wsl / qemu-system-x86_64 / VBoxManage   # only wsl.exe found
(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled  # False
```
Web verification: five official Ubuntu doc pages + secondary cross-checks (see upstream-verification.md).

## 7. Recommended next work unit

**WU-0.2 — Subsystem register** (`docs/subsystem-register.md`, master prompt §6) is the
nominal next step. **However**, the environment blocker in §2 is on the critical path for every
later phase, so the recommended first follow-up is a short **environment-remediation decision**
(enable virtualization in firmware + free disk, or provision an external/isolated Linux builder),
captured as an ADR, **before or alongside** WU-0.2.

Per safety rule §16, this session stops here. The next work unit begins only in a new session
or when the user explicitly asks to continue.
