# Security Policy

> **Pre-Alpha notice.** DevOS does not yet produce signed release images. Do not use it
> in production. The items below describe how we handle reports today; SLAs will tighten
> as the project matures.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately via GitHub's **"Report a vulnerability"** (Security → Advisories) on
this repository, or by contacting a maintainer directly.

Include, where possible:

- A description of the issue and its impact
- Steps to reproduce (a minimal profile/lockfile/command is ideal)
- Affected version / commit
- Any suggested remediation

## What to expect

- **Acknowledgement:** we aim to acknowledge reports within a reasonable window (best
  effort while the project is maintained by volunteers — we will not promise a time we
  cannot meet).
- **Triage:** we assess severity, confirm, and plan a fix.
- **Disclosure:** coordinated. We will credit reporters who wish to be credited.

## Scope of particular concern

Because profiles and lockfiles can drive privileged changes, we care especially about:

- Malicious or tampered profile manifests, lockfiles, or Ansible roles
- Supply-chain issues: unverified artifacts, trust-on-first-use, dependency confusion
- Privilege escalation through `devos`, sudo configuration, or group membership
- Secrets leaking into images, logs, state files, or CI artifacts

## Good-faith research

We will not pursue action against researchers who act in good faith, avoid privacy
violations and service disruption, and give us reasonable time to respond before public
disclosure.
