# fleet-cloud

Fleet Cloud application — a self-hosted fleet/asset tracking platform.

The repository currently owns the **deployment foundation** for the product: a
pinned, isolated Docker Compose stack running upstream **Traccar 6.15.3**
(Apache-2.0) with a dedicated **MySQL 8.0.43** database, fronted by Nginx over
HTTPS at `https://fleet.nazimlaw.com`. Fleet Cloud-specific modules
(maintenance, work orders, reporting, integrations) are built on top of
Traccar's REST API rather than by patching upstream internals.

## Stack

| Component | Choice |
|---|---|
| Tracking core | Traccar `6.15.3-alpine` (Apache-2.0) |
| Database | MySQL `8.0.43` (separate service, no host port) |
| Edge | Nginx origin + Cloudflare (Full strict) |
| Runtime | Docker Compose project `fleet-cloud` on the authorized VPS |

## Repository layout

```
compose.yaml                              pinned Traccar + MySQL stack
.env.example                              non-secret runtime config template
ops/nginx/fleet.nazimlaw.com.conf         Nginx origin site template
ops/traccar/traccar.xml.template          optional XML config reference
scripts/check-deployment-artifacts.py     deterministic deployment checks
docs/adr/                                 architecture decision records
docs/RUNBOOK.md                           deploy / health / upgrade / rollback
docs/plans/                               work plans
```

## Quick start (local validation)

```sh
docker compose --env-file .env.example -f compose.yaml config
python3 scripts/check-deployment-artifacts.py
```

These are the same deterministic checks CI runs. They need no secrets and no
running containers.

## Deployment

- Target: authorized VPS, stack under `/srv/fleet-cloud`, project `fleet-cloud`.
- Health endpoint: `http://127.0.0.1:8082/api/health` (loopback); public
  `https://fleet.nazimlaw.com`.
- Rollback: revert the pinned image tags/revision and `docker compose up -d`
  (database volume preserved). Full procedure in `docs/RUNBOOK.md`.

Actual deployment, secrets creation, Nginx install and Cloudflare/DNS are
performed by trusted local operators — not from CI and not with credentials in
this repository.

## Documentation

- Decisions: `docs/adr/0002-traccar-deployment-foundation.md`
- Operations: `docs/RUNBOOK.md`
- Engineering governance: `AGENTS.md`

## Status

Foundation only. Product requirements beyond tracking, Fleet Cloud modules,
and device onboarding are tracked as separate issues.
