# Recovery, Backup & Rollback

Master-prompt §6.16 (gap #7). Honest about what is implemented vs designed.

## Rollback — what DevOS actually does
- **Profile/tool rollback: implemented.** `devos profile rollback <name> [--to <lockfile>]`
  reinstalls the exact apt versions recorded in a lockfile (dry-run unless `--confirm`). This works
  while those versions remain in the archive. Capture a known-good state with `devos profile lock`.
- **NOT atomic system rollback.** On ext4 there is no whole-OS snapshot rollback. Do not expect to
  "undo" a kernel/base upgrade atomically. (Btrfs/Snapper is a future ADR-0006 evaluation.)

## Backup (user data)
- **Design only; not shipped.** Recommended: choose one of Déjà Dup (GUI), restic, or Borg, with
  encryption and *tested restores*. A default is a Beta-gate decision.
- Config under `/etc/devos` and `~/.config/devos` is plain and backup-friendly (no secrets stored
  there by default).

## Recovery scenarios & current guidance
| Scenario | Current path | Status |
|---|---|---|
| Broken package transaction | `sudo apt --fix-broken install`; re-run `devos profile apply` (idempotent) | guidance |
| Broken optional profile | `devos profile remove <name>` (preserves user data) then re-apply | implemented |
| Wrong tool version | `devos profile rollback <name> --confirm` | implemented |
| Broken kernel/boot | boot a previous kernel from GRUB; Ubuntu recovery mode | inherited, untested |
| initramfs regen | use the **Dracut** tool on 26.04 (detect vs initramfs-tools first) | documented, untested |
| Failed desktop login | switch VT, inspect `journalctl -b`, reinstall gdm3 | guidance |
| Lost FDE recovery key | unrecoverable by design | n/a (FDE deferred) |

## Rescue media
No custom rescue media. Use the **DevOS installer ISO** (or an Ubuntu live ISO) in "try" mode as a
rescue environment to chroot and repair. A tested, documented rescue walkthrough is a Beta-gate item.

## What must be built/tested before Stable
Tested restore of a chosen backup tool · a tested boot-failure recovery walkthrough · Dracut-based
initramfs regeneration tested on the installed image · rescue-media instructions exercised in a VM.
