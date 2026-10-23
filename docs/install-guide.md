# DevOS — Install & Quickstart (experimental)

> Experimental, unsigned-for-production. Run only in a disposable VM.

## 1. Download & verify a release
From https://github.com/sayaksatpathi/DEVOPS-OS/releases:
```bash
sha256sum -c devos-<version>-amd64.qcow2.sha256
cosign verify-blob \
  --certificate devos-<version>-amd64.qcow2.pem \
  --signature   devos-<version>-amd64.qcow2.sig \
  --certificate-identity-regexp 'https://github.com/sayaksatpathi/DEVOPS-OS/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  devos-<version>-amd64.qcow2
```

## 2a. Run the cloud image (QEMU/UEFI)
```bash
qemu-system-x86_64 -machine q35 -accel kvm -cpu host -m 4096 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=OVMF_VARS.fd \
  -drive file=devos-<version>-amd64.qcow2,if=virtio \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0
```
Provide your own cloud-init `user-data` (SSH key) to log in — SSH is key-only by default.

## 2b. Install from the installer ISO
Boot `devos-installer-amd64.iso` in a VM with a blank disk. It performs an unattended
install and bakes in the DevOS profiles. **It wipes the target disk** — use a disposable VM.

## 3. Use the engine
```bash
devos doctor
devos profile list
devos profile apply core           # dry run
devos profile apply core --confirm # install
devos profile lock core            # record exact versions
devos update --system              # preview OS updates
```

See docs/ for architecture, security, and the production roadmap.
