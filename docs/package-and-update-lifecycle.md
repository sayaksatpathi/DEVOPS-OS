# Package & Update Lifecycle

Master-prompt §6.13 (gap #9). What DevOS does today and the policy for OS updates.

## Package management
- APT/dpkg as-is (signed archive). deb822 `ubuntu.sources` preserved. No replacement package
  manager; Snap retained (ADR-0003).
- DevOS tools are installed/removed via `devos profile apply|remove` (idempotent; removal never
  autoremoves/purges, preserving shared deps and user data).
- Verified upstream binaries (e.g. OpenTofu) go to `/usr/local/bin` via the checksum-verified
  `devos_binary` path; they are owned by DevOS, not apt.

## OS updates (kernel, base, security)
- **Check:** `devos update --system` previews whole-OS updates (kernel/base/security) read-only
  (simulated `apt-get dist-upgrade`); it highlights kernel updates. **DevOS never auto-upgrades.**
- **Apply:** the user runs standard Ubuntu tooling (`sudo apt full-upgrade`), then re-locks tools
  with `devos profile lock`.
- **Security updates:** `unattended-upgrades` (Ubuntu default) may apply security fixes; policy is to
  keep it enabled for security-only, and surface pending reboots. `needrestart` behavior inherited.
- **Never freeze vulnerable packages** to preserve a lockfile — lockfiles record state, they are not
  a license to pin a CVE open.

## Release upgrades (`do-release-upgrade`)
- DevOS is a **fresh-image** project. 24.04→26.04 upgrade paths are **not** supported or tested;
  the meta-release `Prompt=lts` behavior is inherited from Ubuntu but unverified for DevOS.
- A DevOS→next-DevOS upgrade story is a Beta/Stable-gate item, not promised now.

## Metadata, disk, interruptions
- Honor apt metadata expiry (anti-replay). No builder-specific mirror/credentials are baked into
  images (verified by image hygiene).
- Disk-full / interrupted-update handling: standard apt recovery (`dpkg --configure -a`,
  `apt --fix-broken install`); DevOS `apply` is idempotent and safe to re-run. VM-level failure
  injection for mid-update interruption is tracked in testing-strategy.md.

## EOL
A DevOS release is EOL when its Ubuntu base leaves standard maintenance (see governance.md).
