# DevOS

> **Status: Pre-Alpha / Phase 0.** No operating system has been built or booted. This repository currently contains Phase 0 planning and audit artifacts only. Nothing here is a release, and no claim of hardware or boot compatibility is made.

`DevOS` (provisional name — subject to trademark, domain, and branding review) is a
planned DevOps-specialized **workstation operating system** built on **Ubuntu 26.04 LTS
Desktop** ("Resolute Raccoon"). Its goal is a general-purpose Ubuntu workstation whose
DevOps toolchains and configuration can be **reconstructed from documented,
version-controlled declarations and verified software inputs**, while the underlying OS
remains understandable, secure, maintainable, and recoverable.

This is **not** a DevOps tool bundle, a terminal app, a theme, or an installer script. It
accounts for the full OS lifecycle: firmware/boot, kernel, hardware, services, storage,
accounts, networking, desktop, packaging, updates, diagnostics, installation, and recovery.

## Current phase

Work is executed in **one scoped work unit per session** (governance rule in
[`DECISIONS.md`](DECISIONS.md) and the master prompt §16/§21). The repository is at the end of:

- **WU-0.1 — Repository, environment, and upstream audit** (this deliverable).

See [`STATUS.md`](STATUS.md) for exactly what exists, what is blocked, and the recommended
next work unit. See [`docs/upstream-verification.md`](docs/upstream-verification.md) for the
verified upstream facts and the discrepancies found.

## Governance & safety (summary)

- Builds/installs/boot tests run **only in disposable, isolated sandbox VMs** — never against
  the host or a real disk.
- No `curl | bash`; artifacts are downloaded from approved sources and verified by
  signature/checksum before use.
- No secrets, keys, or machine identity in source or images.
- No public release, production signing, domain registration, paid infrastructure, or
  physical-hardware testing without explicit approval.
- Features are marked honestly: `implemented` / `tested` / `partially tested` / `planned` /
  `experimental` / `blocked` / `unsupported`. Empty files are never reported as complete work.

## The full-OS vision (and where we are on it)

The goal is that **downloading DevOS gives you a complete operating system that boots and
runs like Ubuntu, with the DevOps toolchains already installed** — not a script you run
afterward. DevOS is an Ubuntu 26.04.1 **derivative**: it boots exactly like Ubuntu (GRUB →
signed kernel → systemd → GNOME); what's different is that the tools are baked in and
reproducible. How that image is built — packages baked into the ISO, or applied at first
boot — is documented in [`docs/build-and-release.md`](docs/build-and-release.md).

**Today:** the engine that installs and pins the packages (`devos` + Ansible) **works and is
tested on real Ubuntu 26.04.1**. The bootable ISO is **not built yet** — it needs a disposable
Linux builder VM (QEMU/OVMF). We've scaffolded the build so it's one step away once a builder
exists; we do not pretend a bootable image exists before it does.

## Try the engine (any Ubuntu, including WSL)

```bash
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos doctor
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos profile validate --all
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos profile apply core      # dry run
```

## Open source & contributing

DevOS is Apache-2.0 licensed so anyone can read, build, extend, and upgrade it. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) to get started, [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
for community norms, and [`SECURITY.md`](SECURITY.md) to report vulnerabilities. CI runs the
unit tests and profile validation on every pull request.

## Repository layout

The target tree is in the engineering charter. Real content exists for the reproducibility
engine (`packages/cli`, `profiles/`, `locks/`, `provision/ansible/`, `tests/`) and the Phase 0
docs; image/installer directories are **scaffolds** clearly marked as not-yet-functional, not
empty placeholders reported as done. See [`STATUS.md`](STATUS.md).

## License

**Apache-2.0** for DevOS's own code and docs (see [`LICENSE`](LICENSE)) — chosen to be
contributor-friendly with an explicit patent grant. This is a provisional baseline pending the
full licensing/trademark review (charter §7.1, §14): any distributed **image** also carries the
licenses of its upstream Ubuntu/third-party contents, and the `DevOS`/`DEVOPS-OS` name remains
subject to trademark clearance before any public release.
