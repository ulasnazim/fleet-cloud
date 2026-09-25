# ADR-0001: Adopt engineering-standard v3.0.0

- **Status:** accepted
- **Date:** 2026-09-25 · **Deciders:** Ulaş Nazım (owner, via issue #1), Forge (implementation owner)

## Context
`fleet-cloud` (`ulasnazim/fleet-cloud`) is a newly created private repository whose only content was an initial `README.md` ("Fleet Cloud application"). Issue #1 asks the repository to adopt the current `ulasnazim/engineering-standard` bundle, v3.0.0 (= Universal Software Engineering Standard 3.0 + Team Development Operating Policy 3.0), through its `AGENT_BOOTSTRAP.md` project-adoption procedure, using governance and repository scaffolding only.

No product requirements, stack, domain, infrastructure, credentials or deployment configuration exists in the repository at adoption time.

## Decision
Adopt engineering-standard v3.0.0 and record it in `AGENTS.md`, preserving the original README. Add the `CLAUDE.md` pointer, the pull-request template, and the `docs/plans/` and `docs/adr/` directories. Describe the repository's remaining gaps in this record rather than fixing them in the same change, as the bootstrap procedure requires.

## Alternatives considered
- **Defer adoption until a stack and product scope are chosen** — rejected: issue #1 requires adoption now, and the bootstrap procedure is deliberately stack-independent.
- **Copy the standard's policy files into this repository** — rejected: the owner-approved `ulasnazim/engineering-standard` `main` is the single top-level policy; duplicating it would create drift and conflicting copies.

## Consequences
- Contributors and agents have a recorded policy version and a local-facts file; unknowns are explicit `TODO(owner)` entries rather than guesses.
- Because the repository holds no code, manifests, tests or deployment configuration, no §18 profiles are selected yet; they will be re-evaluated when the stack lands.
- The gaps below remain open and are proposed as separate work; none is fixed by this adoption.

## Gaps (evidence-based, ranked by risk)

| # | Risk | Gap | Evidence | Proposed issue title |
|---|---|---|---|---|
| 1 | High | No product definition: what Fleet Cloud does, for whom, and its acceptance criteria | README contains only "Fleet Cloud application"; no `docs/BRIEF.md` | Define the fleet-cloud product brief and acceptance criteria |
| 2 | High | No technology stack, manifest or dependency lockfile | Repository tracks only `README.md`; no manifest, lockfile or source tree | Select and document the fleet-cloud stack with a lockfile and an ADR |
| 3 | High | No CI or quality gates, and unknown branch protection | No `.github/workflows/`; branch protection not verifiable from repository files | Add minimal deterministic CI (lint, test, build) and branch protection for fleet-cloud |
| 4 | Medium | No automated tests | No test files or test runner configured | Establish the fleet-cloud test baseline and regression policy |
| 5 | Medium | No `.gitignore` or `.env.example` | Neither file is tracked | Add `.gitignore` and a value-free `.env.example` for fleet-cloud |
| 6 | Medium | No documented deployment target, health endpoint or rollback path, though the authorized VPS is the default future runtime | No deployment files; `AGENTS.md` Deployment section is `TODO(owner)` | Document fleet-cloud deployment target, health endpoint and rollback path |
| 7 | Medium | No data model or audit/recovery design for valuable records | No data access or migration code; `AGENTS.md` recovery section is `TODO(owner)` | Design the fleet-cloud data model with change history and reversible-deletion defaults |
| 8 | Low | No recorded code ownership or review routing | No `CODEOWNERS` or review rules | Define fleet-cloud code ownership and review routing |
| 9 | Low | No proprietary license notice; repositories are proprietary by default | No `LICENSE` or notice file is tracked | Add a proprietary license notice to fleet-cloud |

Risk reflects the likelihood and impact of the gap for a repository not yet in production; absence of source only lowers immediate production risk.

## Not fixed here
All gaps above are intentionally left open per the bootstrap procedure. This ADR records them so they can be triaged as separate issues.
