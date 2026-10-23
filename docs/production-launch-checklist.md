# DevOS — Production Launch Checklist (the human/hardware/legal/funding ~49%)

Everything code can do is done (see docs/PRODUCTION-TODO.md). This is the remaining work that
**only you / people / money can do**, in priority order, with concrete steps. Each item links to
the artifact I already built so the human step is as small as possible.

---

## Phase A — Hardware validation (gate to any real-machine claim)
**Owner: you (+ anyone with spare laptops/desktops). Effort: 1–3 weeks.**
1. [ ] Pick ≥2 physical machines (ideally 1 Intel, 1 AMD; 1 laptop, 1 desktop).
2. [ ] Flash the installer ISO to USB; install on a **spare/disposable disk**.
3. [ ] On each, run `bash tests/hardware/collect.sh > report-<machine>.md` and fill the manual lines.
4. [ ] Test by hand: Wi-Fi, Bluetooth, GPU/display (+ external monitor), suspend/resume,
       battery, audio in/out, webcam, USB, printing. Record pass/fail per row.
5. [ ] Commit the filled rows to `docs/hardware-compatibility.md`.
> Blocks: Beta. No CI substitute exists.

## Phase B — Legal (gate to public naming + distribution)
**Owner: you + a lawyer. Effort: days of your time + legal lead time.**
6. [ ] **Trademark**: search the "DevOS" name in your jurisdiction; if unclear/taken, pick a
       distinctive name. File (or have counsel file). Until cleared, keep "experimental".
7. [ ] **License sign-off**: run `tools/license-inventory.sh`, open the attached
       `license-inventory.tsv` + release SBOM + `licenses.txt`, complete
       `docs/license-review-template.md`, and record the signature.
8. [ ] Assemble the NOTICE/attribution file; confirm Canonical remix/IP-policy compliance.
> Blocks: public release under a name + Stable.

## Phase C — People & governance (gate to a support promise)
**Owner: you. Effort: ongoing recruiting.**
9. [ ] Recruit **≥2 co-maintainers** (see the open call in MAINTAINERS.md). Bus factor must be >1.
10. [ ] Apply branch protection exactly as in `docs/branch-protection.md` (`gh api` one-liner).
11. [ ] Decide the support window + EOL policy; publish it (template in docs/governance.md).
12. [ ] Record the **Stable sign-off** in `docs/release-readiness.md` once B/C/D are met.

## Phase D — Funding & distribution infrastructure (gate to a usable public channel)
**Owner: you. Effort: setup + recurring cost.**
13. [ ] Fund a **security SLA** you can actually staff (targets already in SECURITY.md).
14. [ ] Generate the archive GPG key per `docs/key-custody-runbook.md`; store in an HSM or a
       scoped CI secret `DEVOS_REPO_GPG_KEY`.
15. [ ] Stand up hosting/CDN for images + the apt repo (`packaging/apt-repo/` builds the tree;
        `publish-apt-repo.yml` signs it). Set bandwidth budget + retention.
16. [ ] Publish the public key + the `deb [signed-by=...]` line for users.

## Phase E — Human QA sign-off (gate to accessibility/usability claims)
**Owner: you + a tester (ideally an assistive-tech user). Effort: days.**
17. [ ] Run the manual checklist in `docs/accessibility.md` (screen reader, keyboard-only,
        contrast, audio, printing) on the desktop image. Record results.
18. [ ] Decide installer UX: guided partitioning + a real first-boot credential flow (the
        encrypted/auto variants exist; the UX decision is yours).

---

## Definition of "production / Stable"
All of A–E done **and** the sign-off row in `docs/release-readiness.md` is signed, with
evidence links. Until then DevOS is honestly an **experimental Alpha that is already usable in
VMs/cloud/dev-sandboxes** — which is a real, defensible status, not "not done".

> I (the engineering side) have taken every item to the edge of what software can reach and
> built the artifact for each human step above. Crossing these gates is the ~49% that is, by
> its nature, yours.
