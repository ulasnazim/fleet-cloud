# Fleet Cloud production runbook

Repository-owned deployment package for the Traccar foundation (issue #3).
See `docs/adr/0002-traccar-deployment-foundation.md` for the decisions.

> Deployment, secrets, Nginx and Cloudflare are performed by trusted local
> Lui Dev/Sol on the authorized VPS. This document is the executable procedure;
> no credentials appear here.

## 1. Layout

| Path | Purpose |
|---|---|
| `compose.yaml` | Pinned Traccar + MySQL stack, project `fleet-cloud` |
| `.env.example` | Non-secret runtime configuration template |
| `ops/nginx/fleet.nazimlaw.com.conf` | Nginx origin site template |
| `ops/traccar/traccar.xml.template` | Optional XML reference (not mounted) |
| `scripts/check-deployment-artifacts.py` | Deterministic deployment checks (also run in CI) |
| `.github/workflows/repo-checks.yml` | Least-privilege CI (`contents: read`) |

Runtime directories on the VPS: `/srv/fleet-cloud/` holds the checkout and the
deployment-only `.env`; containers store data in the named volumes below.

## 2. Prerequisites

- Docker Engine with the Compose v2 plugin.
- Root (or sudo) on the VPS.
- The shared host TLS certificate pair already present:
  `/etc/nginx/ssl/nazimlaw.com-origin.pem` and `.key`.
- Nginx with the host convention of per-site files in `/etc/nginx/conf.d/`.

## 3. First deployment

```sh
# 1. Check out the merged revision and record it.
install -d -m 0750 /srv/fleet-cloud
git clone https://github.com/ulasnazim/fleet-cloud.git /srv/fleet-cloud/repo   # if not present
cd /srv/fleet-cloud/repo
git fetch origin && git checkout main && git pull --ff-only
REVISION="$(git rev-parse HEAD)"; echo "deployed revision: ${REVISION}"

# 2. Create the root-owned secrets file (never printed, never committed).
install -m 0600 /dev/null /srv/fleet-cloud/.env
# edit /srv/fleet-cloud/.env using .env.example as the template; generate
# passwords with: openssl rand -base64 36

# 3. Validate before starting.
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml config -q
python3 scripts/check-deployment-artifacts.py

# 4. Start the stack.
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml up -d

# 5. Wait for health.
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml ps
```

## 4. Nginx site

```sh
install -m 0644 ops/nginx/fleet.nazimlaw.com.conf /etc/nginx/conf.d/fleet.nazimlaw.com.conf
nginx -t
systemctl reload nginx
```

`fleet.nazimlaw.com` DNS and Cloudflare proxying use the host TLS pattern
(Cloudflare **Full (strict)** against the origin certificate). DNS is managed
locally by Lui Dev/Sol after resolving the `nazimlaw.com` zone dynamically.

## 5. Health checks

| Check | Command | Expected |
|---|---|---|
| Web/API | `curl -fsS http://127.0.0.1:8082/api/health` | JSON health payload, HTTP 200 |
| Session/API | `curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:8082/api/session` | HTTP 200 (or 401 — endpoint responding) |
| Public HTTPS | `curl -fsSI https://fleet.nazimlaw.com/` | HTTP 200/302 over TLS |
| Containers | `docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml ps` | both `healthy` |

The Traccar container health check uses the transport available in the alpine
image: `wget -q --spider http://127.0.0.1:8082/api/health`.

## 6. Logs

```sh
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml logs -f traccar
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml logs -f database
```

Traccar logs to stdout (for `compose logs`) and to a daily-rotated file in the
`fleet-cloud-traccar-logs` volume. Container stdout is capped by the `json-file`
logging driver (10 MB × 3). SQL logging is disabled (`LOGGER_QUERIES=false`).

## 7. Upgrade

Pin a new immutable tag; never use `latest`.

```sh
cd /srv/fleet-cloud/repo
git fetch origin && git checkout main && git pull --ff-only
# edit compose.yaml to the new pinned tags, then:
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml config -q
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml pull
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml up -d
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml ps
```

Traccar applies required schema migrations on start. Read the upstream release
notes first; back up the database volume before a major upgrade (section 9).

## 8. Rollback / forward recovery

Rollback = return to the previous pinned image tags and revision. The MySQL
data volume is preserved across container restarts.

```sh
cd /srv/fleet-cloud/repo
git checkout <previous-revision>
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml up -d
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml ps
```

Database compatibility: Traccar migrations are forward-only. If a *downgrade*
is required after a schema change, restore the database volume from a
pre-upgrade backup (section 9) rather than running an older image against a
newer schema. Otherwise prefer forward recovery: roll forward to the next
fixed pinned tag.

## 9. Persistent volume inventory (owner-managed backups)

Ulaş manages VPS backups through Hostinger. These volumes/directories need
coverage:

| Volume (compose key) | Docker name | Container path | Contents |
|---|---|---|---|
| `db-data` | `fleet-cloud-db-data` | `/var/lib/mysql` | MySQL data (users, devices, positions) |
| `traccar-data` | `fleet-cloud-traccar-data` | `/opt/traccar/data` | Traccar data |
| `traccar-media` | `fleet-cloud-traccar-media` | `/opt/traccar/media` | Device media (photo/audio/video) |
| `traccar-logs` | `fleet-cloud-traccar-logs` | `/opt/traccar/logs` | Rotated application logs |

Host paths: `/var/lib/docker/volumes/fleet-cloud-*`.

Consistent database backup (run during a quiet window):

```sh
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml exec -T database \
  sh -c 'mysqldump --single-transaction -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' \
  > /srv/fleet-cloud/backup-$(date +%F).sql
```

Never commit or transmit the dump.

## 10. Device protocol port policy

By default **no tracker protocol port (5000–5300) is published**. When a
concrete tracker model/protocol is chosen:

1. Identify the exact TCP/UDP port that protocol listens on (Traccar config
   keys are `[protocol].port`).
2. Publish **only that single port** in `compose.yaml`, e.g.
   `- "0.0.0.0:5043:5043/udp"` for one protocol.
3. Do not publish the whole 5000–5300 range — it starts one `docker-proxy`
   process per port and can leak connections.
4. Record the device model, protocol and port in a follow-up issue/ADR and
   re-run `scripts/check-deployment-artifacts.py`.

## 11. Restart behaviour

Both services use `restart: unless-stopped` and recover automatically after a
host or daemon restart. To verify a controlled restart:

```sh
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml restart
docker compose --env-file /srv/fleet-cloud/.env -f compose.yaml ps   # both healthy
curl -fsS http://127.0.0.1:8082/api/health
```

## 12. Troubleshooting

| Symptom | First checks |
|---|---|
| Traccar unhealthy | `docker compose logs traccar`; confirm `DATABASE_*` values and that `database` is healthy |
| Database unhealthy | `docker compose logs database`; check disk space and `.env` passwords |
| 502 from Nginx | confirm Traccar listens on `127.0.0.1:8082` (`curl http://127.0.0.1:8082/api/health`) |
| WebSocket live view fails | confirm the `Upgrade`/`Connection` proxy headers in the Nginx site |
| Container exits on start | check `docker compose logs <service>`; verify pinned tags were pulled |

## 13. Security notes

- Secrets live only in `/srv/fleet-cloud/.env` (root-owned, mode 0600) and
  container environment; they are never committed, logged or transmitted.
- MySQL has no host port; the web/API port is loopback-only; the dedicated
  network defaults any published bind to `127.0.0.1`.
- Containers run with `no-new-privileges` and CPU/memory/PID limits.
- Traccar's first administrator account is created on first web login; set a
  strong password and complete it during the deployment window.
