# Plan: Isolated OpenCloud file sharing (issue #7)

## Goal
Deliver an auditable, repository-owned deployment package for an isolated
OpenCloud file-sharing service at `https://files.nazimlaw.com` for Ulaş and
Birand, without touching production infrastructure or Traccar data from this
repository.

## Scope (repository only)
- Pinned, isolated Docker Compose stack (`fleet-cloud-opencloud`):
  `opencloudeu/opencloud:7.2.4`, loopback-only proxy on `127.0.0.1:9200`.
- Dedicated network `fleet-cloud-opencloud-net` and named volumes
  `fleet-cloud-opencloud-{config,data}`.
- Non-secret `.env.example`; admin password stays deployment-only.
- Sharing hardening: internal default links, mandatory passwords on public
  links, no demo/self-registration, no external IDP.
- Nginx origin site template for `files.nazimlaw.com` (TLS, forwarding
  headers, SSE/no-buffer, Tus upload size, long timeouts).
- Secrets-free repository export helper (`scripts/export-shareable-files.sh`).
- ADR-0003, OpenCloud runbook (deploy, health, accounts/Space, export,
  upgrade, rollback, persistent data, removal/revocation), README/AGENTS
  updates.
- Extended deterministic checks + least-privilege CI for both stacks.

## Steps
1. Verify the pinned OpenCloud tag exists and the health endpoint semantics
   (`/status.php`, unauthenticated) against upstream docs/source.
2. Confirm the sharing/registration switches and the space-role mapping.
3. Author `ops/opencloud/compose.yaml`, `.env.example` and the Nginx site.
4. Extend `scripts/check-deployment-artifacts.py` and the CI workflow.
5. Write ADR-0003, `docs/RUNBOOK-opencloud.md`, README and AGENTS updates.
6. Render both stacks with synthetic placeholders, run the checks, commit,
   push and open the PR (never merge).

## Verification
- `docker compose --env-file ops/opencloud/.env.example -f ops/opencloud/compose.yaml config` → success.
- `python3 scripts/check-deployment-artifacts.py --opencloud-compose-json <rendered>` → all checks pass.
- Existing `fleet-cloud` checks still pass (regression check).
- CI jobs `deployment-artifacts` → green; `git diff --check` → clean.

## Out of scope / non-goals
Production deployment, DNS/Cloudflare, Nginx host install, account/Space
provisioning, secrets creation, Collabora/web-office, migration of existing
files, and any change to the Traccar/MySQL stack.

## Risks
- New internet-facing authenticated service with two accounts (high) —
  mitigated by isolation, loopback bind, sharing hardening and post-deploy
  verification.
- Upstream env-var/config names for 7.2.4 could drift — verified against the
  `v7.2.4` source tree.
- Runtime stack not exercised locally; host validation remains Lui Dev's step.

## Rollback
Remove the Nginx site/DNS route and stop the `fleet-cloud-opencloud` project,
preserving its data volume; the existing `fleet-cloud` stack is untouched. See
`docs/RUNBOOK-opencloud.md` §10.
