# AGENTS.md: fleet-cloud

Adopted: engineering-standard 3.0.0 on 2026-09-25 by Forge (openrouter/deepseek/deepseek-v4.1-flash), reviewed in PR #2 (https://github.com/ulasnazim/fleet-cloud/pull/2).
Deployment foundation added by Forge for issue #3 (Traccar/MySQL/Nginx/CI).
Governing documents: Universal Software Engineering Standard + Team Development Operating Policy, from `ulasnazim/engineering-standard` (local clone: `~/.engineering-standard/`). This file records **project facts only**. Agents maintain it; humans review changes by PR.

## Product
Fleet Cloud is a self-hosted fleet/asset tracking platform. The current product
scope is the deployment foundation: upstream **Traccar 6.15.3** (Apache-2.0)
tracking core with a dedicated **MySQL 8.0.43** database, served over HTTPS at
`https://fleet.nazimlaw.com`. Fleet Cloud-specific modules (maintenance, work
orders, reporting, integrations) integrate through Traccar's REST API.
Decisions: `docs/adr/0002-traccar-deployment-foundation.md`.
TODO(owner): provide the full product brief (`docs/BRIEF.md`) with users, requirements and acceptance criteria beyond tracking.

## Active profiles (Standard §18)
- **§18.1 Web application** — Traccar serves a browser web UI (device map, reports) behind Nginx.
- **§18.3 API or backend** — Traccar exposes a REST API (`/api/*`) used by the UI and future Fleet Cloud modules.
- **§18.4 Database-heavy** — a dedicated MySQL 8 service stores devices, positions and events.
- **§18.5 Realtime, IoT, telemetry or vehicle-tracking** — the product's core purpose is GPS/telemetry ingestion and tracking.
Not yet evidenced: §18.2 Mobile (no mobile client), §18.6 AI, §18.7 Multi-tenant, §18.8 CLI/worker. Re-select with evidence when those land.

## AI tools and test data
The owner permits private code and customer data with any AI provider. Never put credentials or authentication secrets in prompts, commits or logs. Runtime secrets live only in the root-owned deployment file (`/srv/fleet-cloud/.env`, mode 0600) and are never sent to any model or provider. Test fixtures: none yet — the only automated checks are the deterministic deployment checks below (no secrets, synthetic placeholder values only).

## Verified commands
Verified locally on 2026-09-25 (Docker Compose v2, Python 3):
- Install: No application dependencies yet; `docker compose ... pull` fetches pinned images.
- Develop: TODO(owner) — no application source yet.
- Test all / one file: `python3 scripts/check-deployment-artifacts.py` (static + secret scan); add `--compose-json <file>` for resolved-stack checks. / TODO(owner)
- Type-check: n/a (no typed application code yet).
- Lint + format: none configured; CI runs `git diff --check` for whitespace.
- Build: n/a (images are pulled, not built).
- Smoke test: `docker compose --env-file .env.example -f compose.yaml config` → success and `python3 scripts/check-deployment-artifacts.py` → all checks pass.
- Deploy-validation: `docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml config -q` on the VPS.

## Repository map
- Entry point: `compose.yaml` (Traccar + MySQL stack). · Business logic: TODO(owner) — no product code yet. · Data access and migrations: Traccar-owned (upstream Liquibase migrations run on start). · Tests: `scripts/check-deployment-artifacts.py` + `.github/workflows/repo-checks.yml`.
- Edge config: `ops/nginx/fleet.nazimlaw.com.conf`. · Traccar config reference: `ops/traccar/traccar.xml.template`. · Runtime config template: `.env.example`.
- Plans `docs/plans/` · ADRs `docs/adr/` · Runbook `docs/RUNBOOK.md`.

## Architecture rules
- Traccar is an **unmodified upstream dependency** (pinned image). Do not patch its internals.
- Fleet Cloud modules are separate services/adapters that depend on Traccar through its documented REST API/webhooks; dependency direction is Fleet Cloud module → Traccar API, never the reverse.
- The product's own modules (TODO(owner): to be added) must keep business rules independent of the tracking core and database adapters (Standard §4).
- Access the MySQL service only from within the `fleet-cloud-net` network; never publish the database port.

## Deployment
Target: the authorized VPS is the runtime; one isolated Compose project `fleet-cloud` under `/srv/fleet-cloud` (separate directory, network, volumes, database and least-privilege credentials).
Deployment command: `docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml up -d` (executed by trusted local Lui Dev/Sol, not from CI). · Health endpoint: `http://127.0.0.1:8082/api/health` (loopback), public `https://fleet.nazimlaw.com`. · Rollback path: revert pinned image tags/revision and `up -d` (database volume preserved); forward recovery preferred for schema changes — see `docs/RUNBOOK.md` §8.
Persistent data locations: named volumes `fleet-cloud-db-data`, `fleet-cloud-traccar-data`, `fleet-cloud-traccar-media`, `fleet-cloud-traccar-logs` (host paths `/var/lib/docker/volumes/fleet-cloud-*`).
Credentials: injected at runtime from the root-owned `/srv/fleet-cloud/.env` (never committed); Traccar uses environment-variable configuration. Ulaş separately manages Hostinger backups; all persistent volumes needing coverage are listed in `docs/RUNBOOK.md` §9. Device protocol port policy: no 5000–5300 port published by default (`docs/RUNBOOK.md` §10).
Public DNS/Cloudflare and Nginx install stay with trusted local Lui Dev/Sol. No production infrastructure is changed from this repository or CI.

## Data-change history and recovery (if the product stores valuable records)
The database stores valuable tracking records (devices, positions, events). Traccar owns its schema and audit behaviour upstream; Fleet Cloud has no custom data model yet. Recovery: MySQL volume backup/restore (`docs/RUNBOOK.md` §9) and image/revision rollback (§8).
TODO(owner): document reversible deletion, change/bulk-change audit with actor and sponsoring human, retention and bulk-delete alerts once Fleet Cloud-specific records exist.

## Project-specific rules
- Every image in `compose.yaml` MUST be pinned to an immutable tag; never use `latest`.
- MySQL and other internal services MUST NOT publish host ports; the web/API port MUST bind to `127.0.0.1` only.
- No tracker protocol port range (5000–5300) may be published by default.
- Secrets MUST NOT be committed; only the non-secret `.env.example` is tracked.
- `scripts/check-deployment-artifacts.py` and CI MUST pass before merge; CI uses least privilege (`contents: read`).

## Material human decisions and exceptions (if any)
| Default | Decision and likely consequence | Human | Scope |
|---|---|---|---|
| Stack, product scope and infrastructure are unspecified | Bootstrap is limited to governance and repository scaffolding only | Ulaş (via issue #1) | Adoption PR #2 |
| Pick an open-source tracking core | Use Traccar 6.15.3 (Apache-2.0) + MySQL 8.0.43 to permit proprietary extensions without AGPL network-source obligations | Ulaş (via issue #3) | Deployment foundation PR |
| Prefer TimescaleDB for large telemetry volume | Chosen MySQL 8 as the documented "smaller server" production option and to avoid coupling with the existing PostgreSQL instance; revisit at high volume | Ulaş (via issue #3) | Deployment foundation PR |

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
