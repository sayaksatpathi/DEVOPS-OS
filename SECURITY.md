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

## What to expect (target SLA)

These are the **targets** once the project has ≥2 security maintainers (see MAINTAINERS.md).
Until then they are best-effort and **not guaranteed** — a single volunteer cannot commit to
them, which is exactly why a *funded* SLA + co-maintainers is a hard gate to a Stable release
(docs/release-readiness.md, gap #8).

| Severity | Acknowledge | Triage/assess | Fix target |
|---|---|---|---|
| Critical (RCE, priv-esc, key compromise) | 2 business days | 5 business days | 14 days |
| High | 3 business days | 10 business days | 30 days |
| Medium | 5 business days | 20 business days | next release |
| Low | best-effort | best-effort | backlog |

- **Disclosure:** coordinated; we credit reporters who wish to be credited.
- **Emergency / compromised-key procedure:** revoke, rotate (keyless Sigstore means no long-lived
  key to leak today), publish an advisory, and cut a patched signed release.
- **Honest caveat:** these targets become real commitments only when funded maintainer capacity
  exists. We will not advertise an SLA we cannot staff.

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
