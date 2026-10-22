# Build and Release — how DevOS becomes a full, bootable OS

This document answers the core product question: **how does downloading DevOS give you a
complete operating system — one that boots and runs like Ubuntu — with the DevOps packages
already installed?**

> **Honest status (2026-10-22):** The `devos` engine that installs the packages **works and is
> tested** on Ubuntu 26.04.1. The **active build route is GitHub Actions** (`.github/workflows/
> build-image.yml`), which builds a bootable **cloud image (qcow2)** and boot-tests it under UEFI
> in QEMU — no local builder or hardware change needed. A custom desktop **ISO** remains future
> work. The scripts are written and syntax-checked; the first CI run is the real proof, and we
> iterate on its logs.

## Active route — CI cloud-image build (no local VM needed)

Because the dev host can't run a builder VM, the build runs in GitHub Actions, whose Linux
runners expose `/dev/kvm`. The pipeline (`image/build-cloud-image.sh` + `image/boot-test.sh`):

1. Download Ubuntu's **official 26.04 server cloud image** and verify it against the official
   `SHA256SUMS` (with best-effort GPG authenticity of that file).
2. `virt-customize` the qcow2: copy in the repo, install `ansible-core`, run
   `devos profile apply <profiles> --confirm` **inside the image**, then `devos profile lock`.
3. `virt-sysprep` for image hygiene (reset machine-id + SSH host keys, clear logs/history).
4. **Boot-test** in QEMU/OVMF with a NoCloud seed that verifies the baked-in tools and writes a
   marker to the serial console, then powers off.
5. Upload `devos.qcow2` (+ `.sha256` + serial log) as a downloadable workflow artifact.

**Run it:** on GitHub → **Actions → "Build DevOS image" → Run workflow** (pick profiles), or
push a `v*` tag. Download the artifact and run it locally:

```bash
qemu-system-x86_64 -machine q35 -accel kvm:tcg -cpu max -m 2048 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=OVMF_VARS.fd \
  -drive file=devos.qcow2,if=virtio
```

This is a **real, bootable DevOS** (headless/VM/cloud flavor) with your profiles baked in. The
desktop-ISO path (below) reuses the same engine and comes later.

## The model: Ubuntu base + DevOS layer, baked at build time

DevOS is an **Ubuntu 26.04.1 derivative**. We do not reinvent the kernel, bootloader,
installer, or desktop — a DevOS machine boots exactly like Ubuntu (GRUB → signed shim/kernel
→ systemd → GNOME). What makes it "DevOS" is that the DevOps toolchains are **already
installed and reproducible**.

There are two supported ways to get the packages onto the shipped image. DevOS uses the
same `devos`/Ansible engine in both — that is the whole point of the reproducibility layer.

### Path A — packages baked into the ISO (the "download and it's all there" experience)

```
Ubuntu 26.04.1 Desktop ISO (pinned: URL + SHA256 + GPG)
          │
          ▼  (inside a disposable builder VM)
   mount / unpack the ISO
          │
          ▼
   chroot customization:  devos profile apply <selected profiles> --confirm
          │               (runs the SAME Ansible roles, installing into the image root)
          ▼
   image hygiene:  reset machine-id, remove SSH host keys, clear builder creds/logs,
                   install a first-boot unit (below)
          │
          ▼
   repack → devos-<version>.iso  (+ SHA256, SBOM)
```

The user downloads `devos-<version>.iso`, installs it like Ubuntu, and the DevOps tools are
already present — no post-install step. This is the headline experience the project promises.

### Path B — minimal image + first-boot provisioning

Ship a thin image; on first boot a systemd unit runs `devos profile apply` for the profiles
the user selected. Slower first boot, smaller download, identical end state. Useful for cloud
images and for keeping the ISO small.

Both paths converge because provisioning is declarative: the **profile** says what to install,
the **lockfile** records the exact verified versions, and Ansible applies it — in a chroot at
build time (A) or on the booted system (B).

## First-boot integration (image hygiene + optional apply)

A shipped image must regenerate per-machine identity so every install is unique (never clone
machine-id or SSH host keys). The planned unit (`services/devos-firstboot/`, to be added):

1. Regenerate `/etc/machine-id` and SSH host keys.
2. Optionally run `devos profile apply <profiles>` for Path B.
3. Mark itself complete so it never runs again.

## Build prerequisites (why it needs a VM)

- A **disposable Linux builder** (bare VM or isolated runner) with:
  - Hardware virtualization enabled, QEMU + OVMF (UEFI), optionally `swtpm` for TPM tests.
  - ~60–80 GB free disk per build/test VM; ~150 GB recommended with caches/artifacts.
- The outer host is **orchestration only** — DevOS is never installed onto it.

On the current Windows 11 Home dev host, virtualization is disabled in firmware and free disk
is ~45 GB, so the ISO build is **blocked** until a builder is provided. WSL2 (Ubuntu 26.04.1)
is sufficient for engine/profile/Ansible development but **cannot** build or boot an ISO (it
uses the Microsoft WSL2 kernel, no UEFI/initrd).

## Planned build tooling

- `image/build.sh` (skeleton): orchestrates Path A inside the builder. **Refuses to run** on a
  non-Linux host or without the required tools, rather than producing a broken image.
- Candidate ISO customization tooling (to be chosen via ADR): Ubuntu autoinstall + cloud-init,
  Cubic, or live-build — each must be proven to build, boot, install, and preserve Secure Boot
  on Ubuntu **Desktop** 26.04.1 before adoption.

## Release gates (nothing public until these pass)

Per the project charter, a **public, signed release** requires: pinned verified base image,
image-hygiene verification, SBOM + checksums, security/license/secret scans, a signing-key
custody plan, recovery testing, and legal/trademark review of the `DevOS`/`DEVOPS-OS` name.
Until then, builds stay **local/experimental** and are labelled as such.

## How contributors can build their own (once a builder exists)

```bash
# inside a disposable Ubuntu builder VM with QEMU/OVMF:
sudo ./image/build.sh --profiles core,containers --base <pinned-ubuntu-26.04.1-iso>
# → produces image/out/devos-<version>.iso + .sha256 + SBOM
# then boot-test it in QEMU (never on your real disk).
```

This keeps DevOS fully open and reproducible: the image is just Ubuntu + your chosen profiles,
built by the same engine you can read and run yourself.
