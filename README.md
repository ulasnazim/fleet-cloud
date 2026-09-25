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
| File sharing | OpenCloud `7.2.4` (official unmodified image, isolated stack) |
| Edge | Nginx origin + Cloudflare (Full strict) |
| Runtime | Docker Compose projects `fleet-cloud` and `fleet-cloud-opencloud` on the authorized VPS |

## Repository layout

```
compose.yaml                              pinned Traccar + MySQL stack
.env.example                              non-secret runtime config template
ops/opencloud/compose.yaml                pinned, isolated OpenCloud stack
ops/opencloud/.env.example                non-secret OpenCloud config template
ops/nginx/fleet.nazimlaw.com.conf         Nginx origin site template (tracking)
ops/nginx/files.nazimlaw.com.conf         Nginx origin site template (file sharing)
ops/traccar/traccar.xml.template          optional XML config reference
scripts/check-deployment-artifacts.py     deterministic deployment checks
scripts/check-vendored-sources.py          vendored-source integrity check
scripts/export-shareable-files.sh         secrets-free tracked-file export
vendor/traccar-server/                     upstream Traccar server source v6.15.3 (Apache-2.0)
vendor/traccar-web/                        upstream Traccar web client source v6.15.3 (Apache-2.0)
vendor/README.md                           vendored-source provenance, exclusions, refresh steps
docs/adr/                                 architecture decision records
docs/RUNBOOK.md                           deploy / health / upgrade / rollback (tracking)
docs/RUNBOOK-opencloud.md                 deploy / accounts / Space / rollback (file sharing)
docs/plans/                               work plans
```

## Quick start (local validation)

```sh
docker compose --env-file .env.example -f compose.yaml config
python3 scripts/check-deployment-artifacts.py
```

These are the same deterministic checks CI runs. They need no secrets and no
running containers.

## Vendored upstream source

For direct browsing on GitHub, the **unmodified** upstream Traccar source for
server and web client is vendored as normal tracked files (no submodules) under
`vendor/`, with provenance, licenses, exclusions and a deterministic refresh
procedure documented in `vendor/README.md`. Source is pinned to tag `v6.15.3`:

| Snapshot | Upstream | Commit |
|---|---|---|
| `vendor/traccar-server/` | `traccar/traccar` | `5eb957893c22b988f831200e976b36262d2b8592` |
| `vendor/traccar-web/` | `traccar/traccar-web` | `cfedd3415415623ddbeb74ed6fe6238f3f7a47e0` |

These snapshots are reference source only — they are not built and do not
change the deployed pinned image. Integrity is checked deterministically by
`scripts/check-vendored-sources.py` (also run from the deployment artifact
checks and CI).

## File sharing (OpenCloud)

Ulaş and Birand share files at `https://files.nazimlaw.com` through an
**isolated** OpenCloud `7.2.4` stack (project `fleet-cloud-opencloud`) with its
own network and volumes. It never touches the Traccar/MySQL stack, binds the
proxy to `127.0.0.1:9200` only, uses local identity (no self-registration) and
keeps anonymous/public-link sharing off. See
`docs/adr/0003-opencloud-file-sharing.md` and `docs/RUNBOOK-opencloud.md`.

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

- Decisions: `docs/adr/0002-traccar-deployment-foundation.md`,
  `docs/adr/0003-opencloud-file-sharing.md`
- Operations: `docs/RUNBOOK.md`, `docs/RUNBOOK-opencloud.md`
- Engineering governance: `AGENTS.md`

## Status

Foundation only. Product requirements beyond tracking, Fleet Cloud modules,
and device onboarding are tracked as separate issues.
