# ADR-0003: Isolated OpenCloud file sharing for Fleet Cloud

- **Status:** accepted
- **Date:** 2026-09-25 · **Deciders:** Ulaş Nazım (owner, via issue #7), Forge (implementation owner)
- **Related:** issue #7, ADR-0001 (engineering-standard adoption), ADR-0002 (Traccar foundation)

## Context
Ulaş and Birand need a simple browser/desktop file-sharing surface for Fleet
Cloud. The authorized VPS already runs the isolated Traccar/MySQL stack
(project `fleet-cloud`) behind Nginx/Cloudflare. The file-sharing service must
be internet-facing for two named people, must not weaken or couple to the
tracking stack, and must be deployable by trusted local Lui Dev/Sol without
placing credentials in this repository. Ulaş explicitly approved installing
OpenCloud and the new `files.nazimlaw.com` endpoint on 2026-09-25.

## Decision
Deploy upstream **OpenCloud 7.2.4** (`opencloudeu/opencloud:7.2.4`) as a
**separate, isolated Docker Compose project** `fleet-cloud-opencloud` under
`/srv/fleet-cloud-opencloud`, serving `https://files.nazimlaw.com` behind the
host Nginx/Cloudflare with TLS termination at Nginx.

Concrete repository decisions:
- **Image is pinned** to a released production tag (`7.2.4`, published
  2026-08-21). The rolling tag family (`opencloudeu/opencloud-rolling`,
  `latest`, `daily`) is explicitly forbidden.
- **Isolation:** dedicated Compose project `fleet-cloud-opencloud`, dedicated
  bridge network `fleet-cloud-opencloud-net`, dedicated named volumes
  `fleet-cloud-opencloud-config` (`/etc/opencloud`) and
  `fleet-cloud-opencloud-data` (`/var/lib/opencloud`). No Traccar/MySQL volume,
  host path, `Docker` socket or `.env` is shared. The proxy binds
  `127.0.0.1:9200` only; no internal service port is published.
- **Identity:** the built-in (internal) OpenCloud IDP with local accounts only
  — no Keycloak/external IDP, no demo users, no public/self-registration. Only
  `admin` (Ulaş) and the scoped member account (Birand) exist; accounts are
  created by the admin.
- **Sharing:** new links default to internal (`FRONTEND_DEFAULT_LINK_PERMISSIONS=0`),
  and the public-link storage endpoint is disabled
  (`GATEWAY_STORAGE_PUBLIC_LINK_ENDPOINT=""`). Password enforcement remains
  configured as defense in depth
  (`OC_SHARING_PUBLIC_SHARE_MUST_HAVE_PASSWORD=true` and
  `..._WRITEABLE_...=true`), so anonymous public-link access is unavailable. The
  runbook adds an explicit post-deploy verification step.
- **Space model:** one Space named `Fleet Cloud`. Ulaş is the Space
  manager/admin (`Can manage`); Birand is a non-admin member with `Can edit`
  only. Verified against the OpenCloud space-roles documentation.
- **Configuration is credential-free in the repository.** Only a non-secret
  `.env.example` is committed; the admin password and URL are supplied at
  runtime from the root-owned `/srv/fleet-cloud-opencloud/.env`.
- **Content seeding:** GitHub remains the source of truth. Only a
  secrets-free export of tracked repository files
  (`scripts/export-shareable-files.sh`, `git archive`) is uploaded into the
  Space; the live `/srv/fleet-cloud` deployment tree is never bind-mounted or
  synchronized.
- **Resource limits, health check and restart policy** are set; the rendered
  stack is validated in CI.

## Alternatives considered
- **Reusing the Traccar Nginx site / network / volumes** — rejected: couples a
  new internet-facing authenticated service to production tracking data and
  widens the blast radius of either stack.
- **External IDP (Keycloak)** — rejected for two accounts: adds a service to
  operate without a security benefit at this scale; the internal IDP is the
  upstream-recommended choice for small deployments (≤500 users).
- **OpenCloud rolling image / `latest`** — rejected: the issue forbids
  floating tags; production stability requires a released tag.
- **Public/anonymous link sharing enabled** — rejected: only two named members
  need access, so the public-link storage endpoint is disabled.
- **Bind-mounting or syncing `/srv/fleet-cloud` into the Space** — rejected:
  would expose Traccar runtime data and secrets; only a tracked-file export is
  shared.

## Licensing
- **OpenCloud server is Apache-2.0** (verified against the `v7.2.4` `LICENSE`
  and the image's `org.opencontainers.image.licenses=Apache-2.0` label). The
  separately maintained web client includes copyleft-licensed components; this
  deployment uses the official image unmodified and does not distribute or
  link Fleet Cloud code with it. Ulaş explicitly approved this self-hosted
  OpenCloud deployment in issue #7.
- OpenCloud runs as a **separate, unmodified official container**; this
  repository does not link against or modify its code.
- **Collabora Online / Web Office is not deployed**, avoiding AGPL web-office
  components. If a web-office or other bundled app is added later, its licence
  must be reviewed and approved by the owner first.
- No new paid service or recurring cost is introduced.

## Consequences
- Fleet Cloud gains a browser/desktop file surface for two named users without
  touching the tracking stack or its data.
- Two internet-facing services now exist on the VPS; each is independently
  isolated and rollback-able (remove the Nginx site/DNS route and stop the
  `fleet-cloud-opencloud` project, keeping its volume).
- Operational ownership stays with trusted local Lui Dev/Sol: account
  provisioning, secrets, DNS, Nginx install and the production deployment are
  not performed from this repository or CI.
- Anonymous public sharing is intentionally unavailable; sharing with third
  parties requires a new owner decision and configuration change.
