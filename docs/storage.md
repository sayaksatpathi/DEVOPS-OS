# Storage (§4)

## Done
- **SSD TRIM**: `fstrim.timer` enabled in the baseline (periodic discard).
- **FDE**: LUKS-on-LVM installer variant; unlock verified in CI (#10).

## Encrypted swap (random-key)
On a non-FDE install, enable encrypted swap so secrets paged out are never written in clear:
add to `/etc/crypttab`:
```
cryptswap  /dev/disk/by-partlabel/swap  /dev/urandom  swap,cipher=aes-xts-plain64,size=256
```
and point `/etc/fstab` swap at `/dev/mapper/cryptswap`. On an FDE install swap already sits
inside the LUKS volume, so this is only for non-FDE installs. (Random-key swap disables
hibernation — see below.)

## Hibernation
Hibernation needs a persistent (non-random-key) encrypted swap sized >= RAM and a resume=
kernel arg. It is **off by default** (random-key swap). Document the tradeoff before enabling.

## fstab / UUID
The installer writes UUID-based mounts (subiquity default). Validate with
`findmnt --verify` after install.

## Filesystem choice & Btrfs evaluation
- **Default: ext4** — simplest, well-understood, matches Ubuntu defaults.
- **Btrfs (evaluated, deferred)**: offers snapshots + rollback (Snapper) which would give
  true OS-level rollback (today DevOS only rolls back *profiles*). Costs: more complex
  recovery, performance tuning, and quota semantics. Decision: revisit for Beta if OS-level
  snapshot/rollback becomes a requirement; until then ext4 + restic backups (verified) cover
  the recovery story.

## Not yet automated (needs hardware)
Disk-full behavior on real hardware, Intel RST/VMD NVMe, dual-boot/BitLocker interactions.
