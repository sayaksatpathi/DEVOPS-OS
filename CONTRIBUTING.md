# Contributing to DevOS

Thanks for your interest! DevOS is open source (Apache-2.0) and built so that anyone
can inspect, build, extend, and upgrade it. This guide explains how to get a working
setup and how changes are reviewed.

> **Project status: pre-Alpha.** The reproducibility engine (`devos` CLI + Ansible
> profiles) works and is tested on Ubuntu 26.04.1. The bootable OS image is **not built
> yet** — it needs a Linux builder VM (see [`docs/build-and-release.md`](docs/build-and-release.md)).
> Please read [`STATUS.md`](STATUS.md) before filing issues so expectations match reality.

## Ground rules (non-negotiable)

These come from the project's engineering charter and keep DevOS honest and safe:

1. **Build/boot/install only in disposable VMs** — never against your host or a real disk.
2. **No `curl | bash`.** Download from approved sources and verify signatures/checksums.
3. **No secrets in commits** — keys, tokens, passwords, machine identity. CI scans for them.
4. **Mark work honestly:** `implemented` / `tested` / `partially tested` / `planned` /
   `experimental` / `blocked` / `unsupported`. Never report an empty file as done.
5. **Pin everything.** New tools need an exact version and a verification method; binary
   artifacts need an upstream signature or attestation (not trust-on-first-use).

## Quick start (engine development — works on any Ubuntu, incl. WSL)

```bash
git clone https://github.com/sayaksatpathi/DEVOPS-OS.git
cd DEVOPS-OS
python3 --version            # need >= 3.11
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos doctor
```

Run the tests before every PR:

```bash
PYTHONPATH=packages/cli python3 -m unittest discover -s tests/unit
```

Apply a profile on a **disposable** Ubuntu (or your own WSL dev box):

```bash
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos profile apply core   # dry run
PYTHONPATH=packages/cli DEVOS_ROOT=$PWD python3 -m devos profile apply core --confirm
```

## Adding a profile

1. Add `profiles/definitions/<name>.json` (validate with `devos profile validate <name>`).
2. If it needs an Ansible role, add it under `provision/ansible/roles/`.
3. Add unit tests under `tests/unit/`.
4. Keep the profile declarative; record resolved versions with `devos profile lock <name>`.

## Pull requests

- Keep changes small and focused (one coherent unit per PR).
- All unit tests must pass; CI runs them on every PR.
- Update `STATUS.md` / `CHANGELOG.md` and, for material decisions, `DECISIONS.md`.
- By submitting a PR you agree your contribution is licensed under Apache-2.0
  (see the DCO note below).

## Developer Certificate of Origin (DCO)

Sign off your commits (`git commit -s`) to certify you wrote the code or have the right
to submit it under Apache-2.0. This is a lightweight alternative to a CLA; the policy may
be formalized as the project matures.

## Reporting security issues

Do **not** open a public issue for vulnerabilities. See [`SECURITY.md`](SECURITY.md).
