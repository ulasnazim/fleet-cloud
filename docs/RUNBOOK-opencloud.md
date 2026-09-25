# Fleet Cloud OpenCloud runbook

Repository-owned deployment package for the isolated OpenCloud file-sharing
service (issue #7). See `docs/adr/0003-opencloud-file-sharing.md` for the
decisions.

> Deployment, secrets, DNS, Nginx and account provisioning are performed by
> trusted local Lui Dev/Sol on the authorized VPS. This document is the
> executable procedure; **no credentials appear here**. Never paste a password
> from this runbook's files into GitHub, Telegram, logs, prompts or a command
> line argument.

## 1. Layout

| Path | Purpose |
|---|---|
| `ops/opencloud/compose.yaml` | Pinned OpenCloud stack, project `fleet-cloud-opencloud` |
| `ops/opencloud/.env.example` | Non-secret runtime configuration template |
| `ops/nginx/files.nazimlaw.com.conf` | Nginx final TLS site (Let's Encrypt) |
| `scripts/export-shareable-files.sh` | Secrets-free tracked-file export for the Space |
| `scripts/check-deployment-artifacts.py` | Deterministic deployment checks (also run in CI) |
| `.github/workflows/repo-checks.yml` | Least-privilege CI (`contents: read`) |

Runtime directory on the VPS: `/srv/fleet-cloud-opencloud/` holds this
checkout (as `repo/`) and the deployment-only `.env`. Data lives in the named
volumes below. The live `/srv/fleet-cloud` Traccar tree is **never** read,
mounted or synchronized by this stack.

## 2. Prerequisites

- Docker Engine with the Compose v2 plugin, and `curl` on the host.
- Root (or sudo) on the VPS.
- Nginx with the host convention: site files in `/etc/nginx/sites-available/`,
  enabled by symlinks in `/etc/nginx/sites-enabled/`.
- Certbot already installed and registered, with the shared ACME HTTP-01
  webroot `/var/www/html`. The existing host account is reused; this
  repository never supplies an email address.
- A DNS record for `files.nazimlaw.com` resolving to this host before the
  certificate is requested.
- No existing service listens on host port 9200.

## 3. First deployment

```sh
# 1. Check out the merged revision and record it.
install -d -m 0750 /srv/fleet-cloud-opencloud
git clone https://github.com/ulasnazim/fleet-cloud.git /srv/fleet-cloud-opencloud/repo   # if not present
cd /srv/fleet-cloud-opencloud/repo
git fetch origin && git checkout main && git pull --ff-only
REVISION="$(git rev-parse HEAD)"; echo "deployed revision: ${REVISION}"

# 2. Create the root-owned secrets file (never printed, never committed).
install -m 0600 /dev/null /srv/fleet-cloud-opencloud/.env
# edit it using ops/opencloud/.env.example as the template; generate the admin
# password with: openssl rand -base64 36

# 3. Validate before starting.
docker compose --env-file /srv/fleet-cloud-opencloud/.env \
  -f ops/opencloud/compose.yaml config -q
python3 scripts/check-deployment-artifacts.py

# 4. Start the stack.
docker compose --env-file /srv/fleet-cloud-opencloud/.env \
  -f ops/opencloud/compose.yaml up -d

# 5. Wait for health.
docker compose --env-file /srv/fleet-cloud-opencloud/.env \
  -f ops/opencloud/compose.yaml ps
```

## 4. Nginx site and TLS bootstrap

`files.nazimlaw.com` has no certificate yet, so the first deployment installs
a temporary HTTP-only site, obtains a Let's Encrypt certificate with the
existing Certbot installation/account (non-interactively, without inventing an
email), then installs the final TLS site.

```sh
# 4a. Bootstrap: temporary HTTP-only site serving ACME challenges.
install -d -m 0755 /var/www/html
cat > /etc/nginx/sites-available/files.nazimlaw.com <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name files.nazimlaw.com;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
NGINX
ln -sfn /etc/nginx/sites-available/files.nazimlaw.com \
       /etc/nginx/sites-enabled/files.nazimlaw.com
nginx -t
systemctl reload nginx

# 4b. Obtain the certificate non-interactively (reuses the existing account).
# If Certbot reports that no account exists, STOP and ask the owner for the
# registration email — do not invent one.
certbot certonly --webroot -w /var/www/html -d files.nazimlaw.com \
    --non-interactive --keep-until-expiring

# 4c. Install the final TLS site from this repository and reload.
install -m 0644 ops/nginx/files.nazimlaw.com.conf \
    /etc/nginx/sites-available/files.nazimlaw.com
ln -sfn /etc/nginx/sites-available/files.nazimlaw.com \
       /etc/nginx/sites-enabled/files.nazimlaw.com
nginx -t
systemctl reload nginx

# 4d. Verify renewal and HTTPS.
certbot renew --dry-run
curl -fsSI https://files.nazimlaw.com/status.php
```

Certificates live at `/etc/letsencrypt/live/files.nazimlaw.com/`; the site
includes `/etc/letsencrypt/options-ssl-nginx.conf` and
`/etc/letsencrypt/ssl-dhparams.pem`, matching the other host sites. Cloudflare
proxies `files.nazimlaw.com` with **Full (strict)** against this origin
certificate; DNS is managed locally by Lui Dev/Sol after resolving the
`nazimlaw.com` zone dynamically. The OpenCloud container itself is reachable
only on `127.0.0.1:9200`.

## 5. First login and account provisioning

The built-in `admin` user's initial password is `OPENCLOUD_ADMIN_PASSWORD` in
`/srv/fleet-cloud-opencloud/.env` (root-owned, mode 0600).

1. Read the value in a terminal only, e.g.
   `sudo sed -n 's/^OPENCLOUD_ADMIN_PASSWORD=//p' /srv/fleet-cloud-opencloud/.env`
   — never copy it into a chat, ticket, command argument or log.
2. Sign in once at `https://files.nazimlaw.com` as `admin` (Ulaş).
3. Immediately change the password from the personal profile page and store the
   new value in the owner's password manager.

Provision the second account (Birand) from **Admin Settings → Users**:

- Create a single local account and assign the **User Light** role. Do **not**
  grant the User, Admin or Space Admin role. User Light can participate in an
  assigned Space but cannot create Spaces or public links.
- Set a unique password out-of-band (typed interactively; no email reset will
  fire because no SMTP server is configured). Do not transmit it through
  GitHub/Telegram/logs/prompts.
- Self-registration is unavailable by design: accounts exist only when the
  admin creates them.

## 6. `Fleet Cloud` Space provisioning

Create exactly one Space and apply least privilege:

1. **Files → Spaces → New Space**, name it `Fleet Cloud`.
2. Add members:
   - **Ulaş** — `Can manage` (admin/manager of the Space).
   - **Birand** — `Can edit` only (upload/edit/delete content; cannot manage
     members, quota, enable/disable or delete the Space, and is not an admin).
3. Do not add any other member and do not enable public/anonymous sharing.

Role mapping verified against the OpenCloud space-roles documentation:
`Can edit` = view/download/upload/create/edit/delete content;
`Can manage` adds member/quota/enable management.

## 7. Secrets-free repository export and upload

GitHub is the source of truth; the live `/srv/fleet-cloud` tree is never
shared. Export only git-tracked files (deployment-only `.env` files are
gitignored and therefore never included):

```sh
cd /srv/fleet-cloud-opencloud/repo
scripts/export-shareable-files.sh main /tmp/fleet-cloud-share-export.tar.gz
tar tzf /tmp/fleet-cloud-share-export.tar.gz | grep -E '(^|/)\.env$' || echo "no .env in export"
```

Review the listing, then upload the archive into the `Fleet Cloud` Space
through the web UI (drag and drop) and delete the local tarball. Do not upload
dumps, logs, or any `/srv/fleet-cloud` runtime file.

## 8. Health verification

| Check | Command | Expected |
|---|---|---|
| Loopback readiness | `curl -fsS http://127.0.0.1:9200/status.php` | HTTP 200, status payload |
| Public HTTPS | `curl -fsSI https://files.nazimlaw.com/status.php` | HTTP 200 over TLS |
| Login flow only | `curl -sS -o /dev/null -w '%{http_code}' https://files.nazimlaw.com/` | Redirect/HTML login (no anonymous file listing) |
| Container | `docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml ps` | `healthy` |

The container health check uses `curl -fsS http://127.0.0.1:9200/status.php`
(`/status.php` is an unauthenticated readiness endpoint on the proxy).

### Post-deploy security verification (required)

After provisioning, confirm the hardening is effective — every item must hold:

1. **No public/self-registration:** the login page offers no sign-up/invite
   path, and `https://files.nazimlaw.com/` with no session reaches only the
   login flow (no anonymous browsing).
2. **Anonymous/public-link access disabled:** links default to internal
   (members-only), Birand's User Light role cannot create public links, and the
   public-link storage endpoint is empty. Verify an unauthenticated public-link
   URL cannot retrieve a file. If it can, stop the stack and correct the
   configuration before use.
3. **No guest/anonymous accounts:** Admin Settings → Users lists only `admin`
   and Birand.
4. **Isolation:** `docker compose -p fleet-cloud ps` is unchanged and healthy;
   no `fleet-cloud-opencloud` container is attached to `fleet-cloud-net`.
5. **Bind scope:** `ss -ltnp | grep 9200` shows the listener on `127.0.0.1`
   only (never `0.0.0.0`).

Record the revision and the results. If any item fails, treat it as a
blocker: stop the stack (`docker compose ... down`, data preserved) and report.

## 9. Logs

```sh
docker compose --env-file /srv/fleet-cloud-opencloud/.env \
  -f ops/opencloud/compose.yaml logs -f opencloud
```

OpenCloud logs to stdout; container stdout is capped by the `json-file` driver
(10 MB × 3). Logs must not contain credentials (the admin password is supplied
via environment, not arguments).

## 10. Upgrade

Pin a new released tag; never use `latest`, `rolling` or `daily`.

```sh
cd /srv/fleet-cloud-opencloud/repo
git fetch origin && git checkout main && git pull --ff-only
# edit ops/opencloud/compose.yaml to the new pinned tag, then:
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml config -q
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml pull
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml up -d
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml ps
```

OpenCloud applies any required data migrations on start. Read the upstream
release notes first, and take a pre-upgrade restic/Hostinger snapshot of the
volumes (section 12). Prefer forward recovery to the next fixed tag.

## 11. Rollback

Rollback = return to the previous pinned image tag/revision, or remove the
service. The OpenCloud data volume is preserved across container restarts.

```sh
cd /srv/fleet-cloud-opencloud/repo
git checkout <previous-revision>
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml up -d
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml ps
```

If a downgrade is incompatible with a newer data layout, restore the volumes
from a pre-upgrade snapshot (section 12) instead of running an older image
against newer data. Removing the service entirely is in section 13.

## 12. Persistent data and backups

OpenCloud stores configuration, metadata and file blobs in two named volumes
(the POSIX setup). Ulaş manages VPS backups through Hostinger; these need
coverage:

| Volume (compose key) | Docker name | Container path | Contents |
|---|---|---|---|
| `opencloud-config` | `fleet-cloud-opencloud-config` | `/etc/opencloud` | Instance config and internal secrets |
| `opencloud-data` | `fleet-cloud-opencloud-data` | `/var/lib/opencloud` | Users, spaces, shares, metadata and file blobs |

Host paths: `/var/lib/docker/volumes/fleet-cloud-opencloud-*`.

For a consistent backup, stop the stack first, snapshot/copy **both** volumes,
then start it again:

```sh
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml stop
# snapshot/copy the two volumes with the owner's Hostinger/backup tooling
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml start
```

Never commit or transmit a volume copy or its contents.

## 13. Removal and revocation

```sh
# 1. Revoke access: delete public links, remove members from the Space, then
#    disable/delete the Birand account and change the admin password
#    (Admin Settings) BEFORE removing the service.
# 2. Disable the Nginx site and reload.
rm -f /etc/nginx/sites-enabled/files.nazimlaw.com && nginx -t && systemctl reload nginx
rm -f /etc/nginx/sites-available/files.nazimlaw.com
# 3. Stop and remove the isolated project (containers + network).
docker compose --env-file /srv/fleet-cloud-opencloud/.env -f ops/opencloud/compose.yaml down
# 4. Remove the data only when the owner confirms deletion.
docker volume rm fleet-cloud-opencloud-config fleet-cloud-opencloud-data
# 5. Remove DNS/Cloudflare record (Lui Dev/Sol).
```

The existing `fleet-cloud` Traccar/MySQL stack is untouched throughout.

## 14. Security notes

- Secrets live only in `/srv/fleet-cloud-opencloud/.env` (root-owned, mode
  0600) and container environment; they are never committed, logged or
  transmitted. The live Traccar tree, Docker socket, database files, SSH keys
  and `/var/lib/docker` are not exposed.
- The OpenCloud proxy binds `127.0.0.1:9200` only; no internal service port is
  published. Nginx/Cloudflare is the only HTTPS entry point.
- Local identity only (no external IDP/demo users); accounts are created by the
  administrator. Anonymous/public-link access is disabled by an empty public-
  link storage endpoint; password enforcement remains defense in depth.
- The container runs unprivileged (`1000:1000`) with `no-new-privileges` and
  CPU/memory/PID limits, on its own network and volumes.

## 15. Troubleshooting

| Symptom | First checks |
|---|---|
| Container unhealthy | `docker compose ... logs opencloud`; confirm `OC_URL` is the public HTTPS URL and the volume ownership is `1000:1000` |
| 502 from Nginx | confirm loopback health `curl http://127.0.0.1:9200/status.php`; confirm `proxy_pass http://127.0.0.1:9200` |
| Large upload fails | confirm `client_max_body_size` in the Nginx site and `proxy_request_buffering off` |
| Sync/SSE drops | confirm `proxy_buffering off` and the long `proxy_read_timeout`/`proxy_send_timeout` |
| HTTPS/certificate error | `certbot certificates`; confirm the ACME location serves `/var/www/html`; `certbot renew --dry-run` |
| Login loop / wrong URL | confirm `OPENCLOUD_URL` matches `https://files.nazimlaw.com` and the container was restarted after editing `.env` |
