# Upstream Verification

**Verification date (all entries below): 2026-10-22** unless a row says otherwise.
Method: official Ubuntu documentation fetched directly; third-party sources used only to
cross-check and are labelled as such. Per master prompt §5.2/§7.6, these are **starting
points**, not a substitute for inspecting the exact pinned build artifact and installed
package state once a builder exists.

> **Not yet done in WU-0.1:** no image has been downloaded, mounted, or package-inspected.
> Every "confirmed" below is confirmed *from release notes*, not from the pinned ISO. Each
> item carries a "Re-verify on image" action for the build phase.

## Sources consulted (2026-10-22)

| # | URL | Used for |
|---|-----|----------|
| S1 | https://documentation.ubuntu.com/release-notes/26.04/ | Support lifetime; LTS designation |
| S2 | https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/ | sudo-rs, coreutils, Dracut, cgroup, Wayland, authd, Landscape |
| S3 | https://documentation.ubuntu.com/release-notes/26.04/changes-since-previous-interim/ | GNOME 50, cgroup, TPM/FDE |
| S4 | https://documentation.ubuntu.com/release-notes/26.04/1/ | 26.04.1 point release contents, kernel, Secure Boot issue |
| S5 | https://ubuntu.com/about/release-cycle | Support-end month, flavor policy, ESM |
| B1 | Phoronix / Ubuntu Discourse (blog/forum) | 26.04.1 release date cross-check (secondary) |
| B2 | OSTechNix / LinuxConfig / computingforgeeks (blog) | Feature cross-check (secondary only) |

## Verified facts (official, unless marked)

| Topic | Finding (official wording where quoted) | Source | Status |
|-------|------------------------------------------|--------|--------|
| Base release | Ubuntu 26.04 LTS "Resolute Raccoon", LTS designation; "supported until April 2031" | S1 | Confirmed from notes |
| 26.04.1 point release | Published; point-release notes cover fixes up to and including **2026-08-25**. Secondary sources (B1) give release date **2026-08-27** | S4, B1 | Confirmed (date is secondary-sourced) |
| Kernel | Linux **7.0** (point-release tracker shows `resolute/linux: 7.0.0-15.15`) | S4 | Confirmed from notes |
| HWE stack | **No new HWE stack in 26.04.1**; newer kernel/GPU stack expected with 26.04.2 | S4 + prompt §6.2 | Confirmed |
| GNOME | "The GNOME desktop environment has been updated to version **50**." | S3 | Confirmed from notes |
| Wayland-only | "The *Ubuntu Desktop* session now runs **only on the Wayland back end**, because GNOME Shell can no longer run as an X.org session." (change made in 25.10.) KDE/Xfce still offer X.org. | S2 | Confirmed from notes |
| sudo-rs | "The `sudo-rs` tool is **now the default `sudo` provider**." C sudo "renamed to **`sudo.ws`**" (note: `sudo.ws`, **not** `sudo-ws`). `sudo-ldap` removed → use LDAP via PAM. | S2 | Confirmed from notes |
| coreutils | "The core utilities… are now provided by the **`rust-coreutils`** package." **But `cp`, `mv`, `rm` still come from GNU.** Restore GNU: `sudo apt install coreutils-from-gnu coreutils-from-uutils- --allow-remove-essential`. GNU tools also available via `gnu` prefix (e.g. `gnuls`). | S2 | Confirmed from notes |
| Dracut | "Ubuntu now uses **Dracut** as its default initial ramdisk infrastructure, replacing `initramfs-tools`." "`initramfs-tools` remains supported and you can switch between the two." `update-initramfs` **not mentioned** → recovery tooling must detect the active implementation. | S2 | Confirmed from notes |
| cgroup v1 | "Support for `cgroup` version 1 (`legacy` and `hybrid` hierarchies) has been **removed**." "Ubuntu installations running `cgroup` v1 **will not be allowed to upgrade**." | S2, S3 | Confirmed; cgroup v2 is baseline |
| TPM/FDE | "TPM-backed Full Disk Encryption (TPM/FDE) has been improved." Limitation: "Disk re-encryption is currently not supported." "**Nvidia drivers are the only out-of-tree kernel drivers supported by TPM/FDE.**" | S3 | Confirmed from notes |
| authd | "`authd` can be **installed directly from the Ubuntu archive (universe)**." Not stated as preinstalled/enabled. | S2 | Confirmed — optional, not default |
| Landscape | On this page appears only in the **Ubuntu Pro for WSL** context; no Desktop-ships-enabled statement found. | S2 | Needs separate check |
| Support lifetime (base) | Standard security maintenance **5 years**; ESM/Pro **10 years**. | S1, S5 | Confirmed |

## Image-verified against a live Ubuntu 26.04.1 environment (2026-10-22)

Source: a developer WSL2 instance reporting `VERSION="26.04.1 LTS (Resolute Raccoon)"`,
`VERSION_CODENAME=resolute`. Read-only `dpkg`/`command -v` probes. **Caveat:** this is a
**WSL image**, which uses the Microsoft WSL2 kernel (`6.18…-microsoft-standard-WSL2`) and no
initrd/UEFI — so kernel 7.0, Dracut/initramfs, boot chain, Secure Boot, and TPM/FDE **cannot**
be verified here and still require a QEMU/OVMF VM.

| Topic | Live-image finding | vs release notes |
|-------|--------------------|------------------|
| sudo | `sudo` resolves to `/usr/lib/cargo/bin/sudo` (Rust sudo-rs) | ✅ matches |
| systemd | **259** (259.5-0ubuntu3.4) | ✅ resolves the 258/259 conflict → it is **259** |
| coreutils | `ls`, `cp`, `mv`, `rm` **all** owned by `coreutils-from-uutils`; `coreutils-from-gnu` **not installed**; `gnuls`/`gnucp` present | ⚠️ **contradicts** the summary's "cp/mv/rm still come from GNU" (at least for this image) |
| OS identity | `ID_LIKE=debian`, `UBUNTU_CODENAME=resolute`, `VERSION_CODENAME=resolute` | ⚠️ prompt assumed `ID_LIKE="ubuntu debian"`; actual is **`debian`** only |
| python3 | 3.14.4 (engine needs ≥3.11) | n/a |
| ansible become ↔ sudo-rs | **Finding (acceptance #14):** Ansible `become` with an **interactive** password times out against sudo-rs ("Timed out waiting for become success / interactive authentication is required"); the prompt detection mis-times with sudo-rs. Reliable path: **passwordless sudo scoped to apt** (narrow sudoers drop-in). `ansible-core` from apt = **2.20.1**. | New compatibility result to carry into §6.7 / threat model |

## Discrepancies and unresolved items (WU-0.1 flags these; does not resolve them)

1. **Support-end month conflict.** S1 says "supported until **April 2031**"; S5 (release-cycle)
   says standard maintenance "through **May 2031**", ESM "through May 2036", Legacy "through
   May 2041". → Record both; do not encode a single month into DevOS support policy until the
   exact official month is reconciled. (Prompt §7.7 predicted this conflict.)
2. ~~**cgroup systemd version conflict.**~~ **RESOLVED 2026-10-22:** live 26.04.1 image ships
   **systemd 259** (259.5-0ubuntu3.4), so the "259 removed cgroup v1" wording is correct.
8. **coreutils provenance contradiction (NEW).** Release-notes summary says `cp/mv/rm` stay GNU,
   but the live 26.04.1 image has all of `ls/cp/mv/rm` from `coreutils-from-uutils` with
   `coreutils-from-gnu` absent. → Confirm on the **Desktop ISO** specifically; scripts relying on
   GNU `cp/mv/rm` behavior must be tested, and GNU restoration (`coreutils-from-gnu`) treated as
   an explicit opt-in, not an assumed default.
9. **OS identity (NEW).** Actual `ID_LIKE=debian` (not `ubuntu debian`). → Any installer/detection
   logic keying on `ID_LIKE` must not assume the `ubuntu` token is present.
3. **Flavor support lifetime NOT officially confirmed.** The prompt stated flavors "reportedly
   receive three years." S5 gives **no** flavor duration — says flavors are "community-maintained"
   and "The release cycle for flavours may differ"; directs to each flavor's own site. → Treat the
   3-year figure as **unverified**; confirm per chosen flavor only if a flavor is ever adopted.
   (Alpha-1 targets Ubuntu Desktop GNOME, so this is not yet on the critical path.)
4. **26.04.1 release date is secondary-sourced.** Official point-release page (S4) gives only a
   security-update cutoff of 2026-08-25; the 2026-08-27 date is from Phoronix/Discourse (B1).
   → Confirm the exact date from the official announcement before citing it in policy.
5. **Exact image artifact NOT yet pinned.** No URL/checksum/signature/build-date/architecture has
   been resolved for a specific 26.04.1+ Desktop ISO. This is a **required** Alpha-1 acceptance item
   (§13.2 #4) and remains open. Must be resolved at build time, never floating.
6. **Secure Boot / DKMS concrete risk (verified).** S4 notes: "intel-ipu7 / intel-ipu7-isys modules
   are shipped **unsigned** in latest Resolute kernels, **breaking Secure Boot** systems." → Feed
   into the threat model (WU-0.3) and the Secure Boot ADR.

## Re-verify on the pinned image (build-phase checklist)

- [ ] Resolve and pin exact 26.04.1+ Desktop ISO: URL, SHA256, GPG signature, arch, build date.
- [ ] Confirm GNOME session is Wayland-only on the exact Desktop image; test the supported
      remote-desktop/PipeWire path (GNOME Remote Desktop), not xRDP-on-Xorg.
- [ ] Inspect installed `sudo` provider; test `sudo`, `sudo -l`, password feedback, and Ansible
      `become` against sudo-rs. Note `sudo -E` behavior change.
- [ ] Inspect coreutils provider; test scripts relying on GNU-specific flags; verify `cp/mv/rm`
      are GNU and the `gnu`-prefix fallback works.
- [ ] Detect Dracut vs initramfs-tools on the **installed** system and on **live media**
      separately; use the correct interface for recovery/regeneration.
- [ ] Confirm cgroup v2-only; test container runtimes and legacy images assuming cgroup v1.
- [ ] Confirm systemd version (settles discrepancy #2).
- [ ] TPM/FDE: confirm installer support on target VM/hardware; test recovery-key prompts across
      a firmware change (disposable TPM via swtpm); note Nvidia-only out-of-tree driver support.
- [ ] Landscape and authd: confirm preinstalled vs installer-offered vs archive-only; record
      use/defer decision (ADR 16).
- [ ] `do-release-upgrade` / meta-release behavior; confirm the `Prompt=lts` entry
      (bug 2154602 in S4) and whether 24.04→26.04.1 upgrades are offered. Alpha-1 is fresh-image.
- [ ] Reconcile support-end month (discrepancy #1) from current official docs before any support promise.
