# ADR-0002: Traccar foundation for Fleet Cloud

- **Status:** accepted
- **Date:** 2026-09-25 · **Deciders:** Ulaş Nazım (owner, via issue #3), Forge (implementation owner)
- **Related:** issue #3, ADR-0001 (engineering-standard adoption)

## Context
Fleet Cloud needs a production-ready, self-hosted foundation for vehicle/asset
tracking that can be extended with Fleet Cloud-specific modules without
rewriting GPS ingestion, device protocol support or the web/API layer. The
authorized VPS is the default runtime; Cloudflare fronts public TLS and Nginx
is the origin. No product requirements beyond tracking exist yet, and no
maintenance/work-order workflow may be claimed to be covered by the base.

## Decision
Use upstream **Traccar 6.15.3** (`traccar/traccar:6.15.3-alpine`) as the
open-source tracking core, backed by a dedicated **MySQL 8.0.43**
(`mysql:8.0.43`) service, deployed as an isolated Docker Compose stack
(project `fleet-cloud`) with Nginx terminating TLS for
`https://fleet.nazimlaw.com`.

Concrete repository decisions:
- **Images are pinned** to immutable release tags (no `latest`).
- **Isolation:** dedicated Compose project `fleet-cloud`, dedicated bridge
  network `fleet-cloud-net`, separate named volumes for the database and for
  Traccar data/media/logs. MySQL publishes no host port; the Traccar web/API
  port binds to `127.0.0.1:8082` only and is published to the host via Nginx.
- **Port policy:** no tracker protocol port in 5000–5300 is published. A
  tracker port is added only after a concrete device model/protocol is chosen.
- **Configuration is credential-free in the repository.** Traccar is
  configured through upstream-supported environment variables
  (`CONFIG_USE_ENVIRONMENT_VARIABLES=true`); secrets are supplied at runtime
  from a root-owned deployment file (`/srv/fleet-cloud/.env`). Only a
  non-secret `.env.example` is committed. `ops/traccar/traccar.xml.template`
  documents the equivalent XML keys but is not mounted by default.
- **Resource limits, health checks and restart policy** are set for both
  services; `docker compose config` is validated in CI.

## Alternatives considered
- **Fleetbase** — broad logistics feature set, but AGPL-3.0 would impose
  source-disclosure obligations on network-served modifications unless a
  commercial licence were purchased, which issue #3 rules out.
- **Small/early fleet-maintenance projects** — lower adoption, maturity and
  protocol coverage; higher long-term maintenance risk.
- **TimescaleDB (PostgreSQL)** as the database — recommended by Traccar for
  large installations; MySQL was chosen because it is the documented
  "smaller server" production option and the VPS already runs PostgreSQL for
  other projects, so a separate engine avoids coupling and shared-instance
  blast radius. Revisit if telemetry volume grows.
- **H2 (default embedded database)** — rejected: not recommended upstream for
  production.
- **Editing Traccar internals directly** — rejected; see extension strategy.

## Licensing
- **Traccar is Apache-2.0** (verified against the `v6.15.3` `LICENSE.txt`).
  Proprietary Fleet Cloud modules and repository code may be added without
  network-source obligations.
- **MySQL Community Server is GPL-2.0** (with the FOSS licence exception). It
  runs as a separate, unmodified official container; Fleet Cloud code does not
  link against or modify MySQL, so no copyleft obligation reaches this
  repository or its proprietary modules. Only the client JDBC driver shipped
  inside Traccar is used, via Traccar's own licensing.
- No copyleft dependency is introduced into repository-owned code.

## Extension strategy
Fleet Cloud-specific behaviour (maintenance, work orders, reporting,
integrations) is built as separate services/modules that integrate with
Traccar through its documented **REST API and webhooks/forwarding**, not by
patching upstream internals. This keeps upgrades to new Traccar releases a
container-tag change and preserves the Apache-2.0 boundary. The first concrete
module and its API contract are future issues.

## Consequences
- Fleet Cloud gains a production-grade tracking foundation with an auditable,
  deterministic deployment package and CI.
- Product requirements beyond tracking, work-order modules, and device
  onboarding remain open (issue #3 non-goals).
- Operational ownership stays with trusted local Lui Dev/Sol: deployment,
  secrets, Nginx and Cloudflare are not performed from this repository.
- MySQL rather than TimescaleDB may become a scaling limit at very high
  telemetry volume; the JDBC URL and compose service are the only places to
  change if it is revisited.
