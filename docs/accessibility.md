# Accessibility, Audio, Input & Printing

Gap #11. Code can check that the components are *present and enabled*; it cannot verify the
*experience* — that a screen reader actually reads the installer, audio actually plays, a
printer actually prints. Those require a human (and hardware). This file splits the two.

## Automated presence checks (added to the desktop image boot test)
The desktop verify seed asserts, when a GNOME desktop is present:
- `gdm3` enabled (login reachable)
- `gnome-shell` installed
- (planned) `orca` (screen reader) + `at-spi2` present; `cups` (printing) + `pipewire` (audio) services available

These prove the pieces ship; they do **not** prove usability.

## Manual QA checklist (needs a human + hardware)
### Accessibility
- [ ] Installer is fully keyboard-navigable (no mouse)
- [ ] Orca screen reader reads the installer and desktop
- [ ] High-contrast theme + large text work
- [ ] Zoom/magnifier works
### Audio
- [ ] Output to speakers/headphones works; volume + mute work
- [ ] Microphone captures; Bluetooth audio pairs and plays
### Input
- [ ] Keyboard layouts / input methods switch correctly
- [ ] Touchpad gestures, external mouse work
### Printing/scanning
- [ ] A CUPS-discovered printer prints a test page
- [ ] A scanner (if present) scans

## Status
- **Presence checks:** automatable — being added.
- **Experience QA:** `blocked-human` — requires a tester with the relevant hardware and, for
  accessibility, ideally a user of assistive technology. This cannot be closed in CI.
