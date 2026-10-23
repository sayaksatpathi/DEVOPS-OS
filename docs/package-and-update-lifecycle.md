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

## Reproducibility vs. security updates (the lockfile tension)

Pinning apt packages to exact versions from the lockfile gives reproducibility **only while
those versions remain in the live archive**. Ubuntu's archive keeps just the current version
of each package, so a security update supersedes a pinned version and the pin stops resolving.
Hard-failing on that would also violate the rule *never freeze a vulnerable package to satisfy
a stale lock*. Therefore DevOS uses **best-effort pinning**:

1. `apply` tries the lockfile-pinned `name=version`.
2. If a pin is unavailable (archive moved), it installs the latest and emits a loud
   `REPRO_DRIFT` notice — you then re-lock (`devos profile lock`) to capture the new state.

**Strict, time-stable reproducibility** requires a *snapshot archive*, not the live one:
pin apt sources to **snapshot.ubuntu.com** at a recorded timestamp and record that timestamp
in the lockfile. DevOS implements this: set `DEVOS_APT_SNAPSHOT=<YYYYMMDDTHHMMSSZ>` at build time and
the provisioning pins apt to that snapshot (deb822 `Snapshot:` field). The default
engine does best-effort pinning + drift reporting, which is honest about when reproducibility
was broken by an archive move.

## EOL
A DevOS release is EOL when its Ubuntu base leaves standard maintenance (see governance.md).
