# Developer Certificate of Origin (DCO)

DevOS uses the **DCO** (not a CLA) — lightweight and standard. Every commit must be
signed off, certifying you have the right to submit it under the project's license:

```
git commit -s -m "your message"
```

which appends `Signed-off-by: Your Name <you@example.com>`. By signing off you agree to the
DCO 1.1 (https://developercertificate.org/). PRs with unsigned commits are not merged.
This is enforced via a DCO check (branch protection, see docs/branch-protection.md).
