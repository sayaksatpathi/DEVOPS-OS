# Subsystem Register

Every OS subsystem (master-prompt §6), its implementation strategy, and honest status.
**Strategy:** inherited (Ubuntu as-is) · configured · extended · replaced · experimental · planned.
**Status:** implemented · tested · partial · planned · blocked · unsupported.
Last updated 2026-10-22. This register is a WU-0.2 deliverable and is maintained going forward.

## 6.1 Firmware, boot, startup
| Item | Strategy | Status | Notes / test / recovery |
|---|---|---|---|
| UEFI boot, GRUB, shim/kernel chain | inherited | tested (VM) | Cloud + desktop images boot under OVMF in CI. BIOS/CSM unsupported (v1). |
| Secure Boot (signed chain) | inherited | **blocked** | Ubuntu-signed chain reused; end-to-end SB **not verified** (needs enrolled OVMF SB vars). Known risk: unsigned intel-ipu7 modules break SB (upstream-verification). |
| initramfs | inherited | partial | Dracut is the 26.04 default; recovery tooling must detect Dracut vs initramfs-tools. Not exercised (cloud image uses it; not tested). |
| Emergency/recovery boot | inherited | planned | No tested rescue path yet. |

## 6.2 Kernel & core OS
| Linux generic 7.0 | inherited | tested (boots) | cgroup v2 only (v1 removed). HWE policy: ADR open. |
| cgroup v2 workloads | configured | partial | Podman profile installs; rootless workflow not load-tested. |

## 6.3–6.4 CPU, devices, drivers
| x86-64 device/driver stack | inherited | **blocked** (VM only) | No physical hardware tested. DKMS/third-party modules: avoided. |

## 6.5 Services & processes (systemd) | inherited | tested (boots) | DevOS adds no always-on daemon. `devos` is unprivileged. |

## 6.6 Storage, filesystems, clocks
| ext4 baseline, GPT/ESP | inherited | partial | Installer uses `direct` layout (tested via autoinstall ISO). No atomic rollback (ext4). Btrfs/Snapper: future ADR. |
| Full-disk encryption | planned | **blocked** | TPM/FDE ADR open; not implemented. |

## 6.7 Users, auth, authorization
| First-user, sudo-rs, PAM, polkit | inherited/configured | partial | sudo-rs `become` characterized (needs passwordless for automation). Installer forces password change on first login (no persistent default). |

## 6.8 Networking & time | inherited | partial | NetworkManager/systemd-resolved as-is. DNS-vs-cluster conflicts (minikube/kind) documented as risk, not tested. |

## 6.9 Desktop (GNOME Wayland) | inherited | partial | Desktop image installs ubuntu-desktop-minimal + gdm3, boots to multi-user; **reaching a GNOME session not yet asserted** (gap #4). Remote desktop (GNOME RD/PipeWire): ADR open. |

## 6.10 Audio/input/a11y/locale | inherited | planned | Not configured or tested beyond Ubuntu defaults. |

## 6.11 Power & laptop | inherited | **blocked** | Requires physical hardware. |

## 6.12 Packages & apps (APT/dpkg/Snap)
| APT provisioning, deb822 | configured | tested | `devos apply` installs via apt, idempotent. Upstream identity preserved (`/etc/devos-release`, not overwriting os-release). Snap retained. |
| Verified upstream binaries | extended | tested | `verify.py` gate + `devos_binary` role (OpenTofu). |

## 6.13 Updates & lifecycle | planned | **not addressed** | OS kernel/base update + `do-release-upgrade` story unwritten (gap #9). `devos update` checks tool updates only. |

## 6.14 Logging & diagnostics | inherited | partial | journald as-is; `devos doctor`/`logs` basic. No diagnostic-bundle redaction yet. |

## 6.15 Installer & first boot | configured | partial | Autoinstall ISO builds + installs in CI (core). First-boot machine-id/SSH-host-key reset via virt-sysprep (cloud image). Full install→reboot→login not yet asserted (gap #1). |

## 6.16 Backup, recovery, rollback | planned | **not built** | Design only. No rescue media, no tested restore, no rollback. |

## 6.17 Image hygiene & identity | configured | tested | machine-id + SSH host keys reset; builder creds/logs cleared (virt-sysprep). cloud-init state cleaned. |

## 6.18 Basic desktop UX | inherited | partial | Comes from ubuntu-desktop-minimal; not independently tested. |

## Summary
Boot/packaging/provisioning/hygiene: **implemented & VM-tested**. Security-critical
(Secure Boot, TPM/FDE, recovery), hardware, updates, a11y, desktop-session depth:
**planned or blocked**. See `docs/testing-strategy.md` and `known-issues.md`.
