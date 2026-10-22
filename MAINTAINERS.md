# Maintainers

> **Bus factor is currently 1 — this is a known risk (gap #9).** DevOS needs co-maintainers
> before it can carry a stable-release support promise. This file is the structure and the
> open call; it cannot conjure people — that step is human.

## Current maintainers
| Handle | Areas | Role |
|---|---|---|
| @sayaksatpathi | all (engine, image, CI, release) | lead / BDFL (provisional) |

## We are looking for co-maintainers
Especially for: **security response**, **hardware QA** (people with physical machines),
**installer/desktop**, and **release engineering**. Opening an issue titled "co-maintainer: <area>"
with your background is the way in.

## Becoming a maintainer
1. Land several substantive PRs (green CI, honest status markers).
2. Help triage issues / reviews for a while.
3. An existing maintainer nominates you; lead approves.
4. You get commit + release rights for your area.

## Maintainer responsibilities
- Review PRs in your area; enforce the CONTRIBUTING ground rules (no secrets, pinned deps,
  honest status, disposable-VM-only testing).
- Share the security-response rotation (see SECURITY.md).
- Cut releases per docs/governance.md; never mutate a published release.

## Decision making
Material decisions go through an ADR (docs/adr) + DECISIONS.md. Lead breaks ties until a
formal governance model is adopted (a Stable-gate item).

## Continuity plan
Until there are ≥3 maintainers, treat every release as experimental and say so. A single
maintainer cannot meet a production security SLA — that is why "funded SLA + co-maintainers"
is a hard gate to Stable (docs/release-readiness.md).
