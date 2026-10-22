## DevOS — experimental cloud image

> ⚠️ **Experimental / pre-Alpha. Unsigned. Not for production.** This image is built
> automatically in CI from source and has not undergone a security, signing, or release
> review. Run it only in a disposable VM. Do not install it on a machine you care about.

A bootable **DevOS cloud image** (qcow2): the official Ubuntu 26.04.1 server cloud image with
the DevOS DevOps profiles baked in by the `devos` engine, boot-tested under UEFI in CI.

### What's inside
- Base: Ubuntu 26.04.1 LTS (Resolute Raccoon) official cloud image, checksum + GPG verified.
- Profiles baked in: **core** (git, openssh-client, curl, jq, ca-certificates) and
  **containers** (rootless Podman + userspace networking/storage).
- Per-machine identity reset (machine-id + SSH host keys regenerate on first boot).

### Verify the download
```bash
sha256sum -c devos-<version>-amd64.qcow2.sha256
```

### Run it (QEMU, UEFI)
```bash
qemu-system-x86_64 -machine q35 -accel kvm -cpu host -m 4096 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=OVMF_VARS.fd \
  -drive file=devos-<version>-amd64.qcow2,if=virtio \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0
```
It's a cloud image, so log in via your own cloud-init `user-data` (set a user/SSH key), or use
it as a base in a cloud/VM platform.

### Not included (yet)
- A desktop (GNOME) ISO — this is the server/cloud flavor. The same pipeline extends to it.
- Signed artifacts / production trust. See `docs/build-and-release.md` and `SECURITY.md`.

Built by the open-source pipeline in this repo — reproduce it yourself via
**Actions → Build DevOS image**, or `git tag v… && git push --tags`.
