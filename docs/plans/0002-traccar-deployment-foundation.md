# Plan: Traccar deployment foundation (issue #3)

## Goal
Deliver an auditable, repository-owned deployment package for a self-hosted
Traccar foundation at `https://fleet.nazimlaw.com`, ready for incremental Fleet
Cloud development, without touching production infrastructure from this repo.

## Scope (repository only)
- Pinned Docker Compose stack (`fleet-cloud`): Traccar `6.15.3-alpine` + MySQL `8.0.43`.
- Non-secret `.env.example`; runtime secrets stay deployment-only.
- Traccar configuration template (MySQL, UTC, proxy/base URL, safe logging).
- Nginx origin site template with WebSocket + forwarding headers.
- ADR, runbook, device-protocol port policy, persistent-volume inventory.
- README/AGENTS updates with product purpose, profiles, commands, deployment.
- Deterministic validation script + least-privilege CI.

## Steps
1. Verify pinned image tags exist; confirm Traccar's `v6.15.3` Docker env-var
   configuration and health endpoint.
2. Author `compose.yaml` with isolation, limits, health checks, loopback bind.
3. Add `.env.example`, `.gitignore`, Nginx and Traccar templates.
4. Add `scripts/check-deployment-artifacts.py` and the CI workflow.
5. Write ADR-0002, `docs/RUNBOOK.md`, README and AGENTS updates.
6. Run `docker compose config` and the check script; commit, push, open PR.

## Verification
- `docker compose --env-file .env.example -f compose.yaml config` → success.
- `python3 scripts/check-deployment-artifacts.py --compose-json <rendered>` → all checks pass.
- CI job `deployment-artifacts` → green.
- Secret scan → no matches; no `.env` tracked.

## Out of scope / non-goals
Production deployment, secrets creation, Nginx install, Cloudflare/DNS,
device onboarding, tracker protocol ports, maintenance/work-order modules.

## Risks
- MySQL vs TimescaleDB at very high telemetry volume (documented; revisitable).
- Config/env key names must match Traccar 6.15.3 (verified against upstream docs).
- Full runtime stack not exercised locally; host validation is Lui Dev's step.

## Rollback
Revert the pinned image tags/revision and `docker compose up -d`; database
volume preserved. See `docs/RUNBOOK.md` §8.
