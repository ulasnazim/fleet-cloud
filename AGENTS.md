# AGENTS.md: fleet-cloud

Adopted: engineering-standard 3.0.0 on 2026-09-25 by Forge (openrouter/deepseek/deepseek-v4.1-flash), reviewed in the adoption pull request linked to issue #1.
Governing documents: Universal Software Engineering Standard + Team Development Operating Policy, from `ulasnazim/engineering-standard` (local clone: `~/.engineering-standard/`). This file records **project facts only**. Agents maintain it; humans review changes by PR.

## Product
Fleet Cloud application (per the repository README). Product purpose, users, requirements and domain are not yet defined in this repository.
TODO(owner): provide a product brief (`docs/BRIEF.md`) with purpose, users and requirements.

## Active profiles (Standard §18)
None selected yet: the repository contains no application code, manifests, lockfile, tests or deployment configuration, so no §18 profile can be evidenced.
Rejected for now (no evidence): §18.1 Web application, §18.2 Mobile application, §18.3 API/backend, §18.4 Database-heavy, §18.5 Realtime/IoT/telemetry, §18.6 AI-enabled software, §18.7 Multi-tenant software, §18.8 CLI/automation/background-worker.
TODO(owner): re-select profiles and record one line of evidence each when the stack and product scope are decided.

## AI tools and test data
The owner permits private code and customer data with any AI provider. Never put credentials or authentication secrets in prompts, commits or logs. Project-specific test fixtures: TODO(owner) — no tests or fixtures exist yet.

## Verified commands
No install, develop, test, build or smoke commands are defined in this repository yet (no manifest or lockfile is present, so nothing could be verified). TODO(owner): record verified commands once a stack is chosen.
- Install: TODO(owner)
- Develop: TODO(owner)
- Test all / one file: TODO(owner) / TODO(owner)
- Type-check: TODO(owner)
- Lint + format: TODO(owner)
- Build: TODO(owner)
- Smoke test: TODO(owner)

## Repository map
- Entry point: TODO(owner) · Business logic: TODO(owner) · Data access and migrations: TODO(owner) · Tests: TODO(owner)
- Plans `docs/plans/` · ADRs `docs/adr/` · Runbook `docs/RUNBOOK.md` (TODO(owner): not yet created)

## Architecture rules
No code yet; no dependency directions or module boundaries are present.
TODO(owner): document allowed dependency directions and module boundaries once modules exist.

## Deployment
Target: the authorized VPS is the default future runtime per issue #1, but runtime provisioning is out of scope and no deployment configuration exists in this repository.
Deployment command: TODO(owner) · Health endpoint: TODO(owner) · Rollback path: TODO(owner) · Persistent data locations: TODO(owner).
Ulaş separately manages Hostinger backups. TODO(owner): document how this app receives credentials and the scoped deployment access method once deployment is defined.

## Data-change history and recovery (if the product stores valuable records)
Unknown — no product data model exists yet.
TODO(owner): when the product stores valuable records, document reversible deletion, create/update/delete and bulk-change audit history with actor and sponsoring human, retention, bulk-delete alerts and verified recovery.

## Project-specific rules
None.

## Material human decisions and exceptions (if any)
| Default | Decision and likely consequence | Human | Scope |
|---|---|---|---|
| Stack, product scope and infrastructure are unspecified | Bootstrap is limited to governance and repository scaffolding only; no product requirements, stack, domain, credentials, deployment resources or paid services were created or assumed | Ulaş (via issue #1) | This repository, adoption pull request |

## Portable core (for agents without the global policy installed; do not edit)
- Never commit, log or send credentials, authentication secrets or `.env` secrets to AI providers; private code and customer data may go to any AI provider for the task.
- Prefer branch and issue for meaningful work; avoid force-push to shared branches. Any team member may deploy within existing authority, including with a disclosed engineering exception. An agent may execute a named member's scoped deployment. Log the revision and checks run or skipped.
- Small focused changes; Conventional Commits; validate input; authorise server-side; parameterised queries.
- Tests for behaviour changes and regressions; run lint, type-check, tests and build before the PR.
- New backward-compatible migrations only; never edit an applied migration.
- Valuable records: reversible deletion when appropriate, automatic change/deletion audit with actor and sponsoring human for agent actions, unusual bulk-delete alert and tested recovery. Obsidian can contain summaries but is not the audit source.
- Readable code; comments explain why; no dead code or debug output; justify new dependencies; no copyleft without owner approval.
- Same step fails twice → stop and report. Do not invent commands or results.
- A human developer may choose engineering exceptions without a new approval gate. Flag material risk once, follow the authorized decision, and record a short reason/consequence. Destructive production data changes, permission escalation and paid purchases still need a decision by someone empowered to make it. Owner account/access/budget authority persists. Report what changed, what was checked or skipped, and deployment status honestly.
