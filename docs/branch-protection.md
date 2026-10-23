# Branch Protection (governance §16)

Apply these to `main` (Settings → Branches → Add rule), or via `gh api`:

- Require a pull request before merging; **1 approving review**; dismiss stale approvals.
- Require **CODEOWNERS** review.
- Require status checks to pass before merging, **up to date**:
  - `unit-tests (3.11)`, `unit-tests (3.12)`, `ansible-lint`, `secret-scan`
- Require **signed commits** (and DCO sign-off, see docs/dco.md).
- Require linear history; no force-push; no deletions.
- Include administrators.

`gh` example:
```bash
gh api -X PUT repos/sayaksatpathi/DEVOPS-OS/branches/main/protection \
  -f required_status_checks.strict=true \
  -f 'required_status_checks.contexts[]=unit-tests (3.11)' \
  -f 'required_status_checks.contexts[]=ansible-lint' \
  -f enforce_admins=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f restrictions=
```
> Applying this requires repo-admin rights — it is an operator action, documented here so it
> is one command away.
