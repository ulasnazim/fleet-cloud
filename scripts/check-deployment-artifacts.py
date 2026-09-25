#!/usr/bin/env python3
"""Deterministic checks for the repository-owned fleet-cloud deployment artifacts.

Runs two kinds of checks:

  1. Static checks over tracked files (compose.yaml, .env.example, .gitignore,
     ops/nginx/fleet.nazimlaw.com.conf, ops/traccar/traccar.xml.template,
     docs/RUNBOOK.md).
  2. A high-signal secret scan over every git-tracked text file, plus a check
     that no runtime secret file (.env) is tracked.

When ``--compose-json`` points at the output of
``docker compose config --format json`` the resolved stack is also validated
(images pinned, no public database port, loopback-only web port, no tracker
protocol range published, health checks, resource limits, restart policy,
named volumes and the dedicated network).

Exit code 0 means every check passed. Any failure prints a ``FAIL`` line and
the script exits 1. No network access and no Docker daemon are required for the
static and secret checks.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TRACKER_PORT_RANGE = range(5000, 5301)
REQUIRED_FILES = [
    "compose.yaml",
    ".env.example",
    ".gitignore",
    "ops/nginx/fleet.nazimlaw.com.conf",
    "ops/traccar/traccar.xml.template",
    # Isolated OpenCloud file-sharing stack (issue #7).
    "ops/opencloud/compose.yaml",
    "ops/opencloud/.env.example",
    "ops/nginx/files.nazimlaw.com.conf",
    "scripts/export-shareable-files.sh",
    "docs/RUNBOOK-opencloud.md",
    # Vendored upstream Traccar source snapshots (issue #11).
    "scripts/check-vendored-sources.py",
    "vendor/README.md",
    "vendor/traccar-server.sha256",
    "vendor/traccar-web.sha256",
    "vendor/traccar-server/LICENSE.txt",
    "vendor/traccar-web/LICENSE.txt",
]

# High-signal credential patterns. Deliberately narrow to avoid noise.
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bgh[posru]_[A-Za-z0-9]{30,}\b"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"), "GitHub fine-grained token"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"), "generic sk- API key"),
]

failures: list[str] = []
checks = 0


def ok(message: str) -> None:
    global checks
    checks += 1
    print(f"PASS: {message}")


def fail(message: str) -> None:
    global checks
    checks += 1
    failures.append(message)
    print(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    (ok if condition else fail)(message)


def git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        require((REPO_ROOT / rel).is_file(), f"tracked file present: {rel}")


def check_compose_static() -> str:
    text = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")
    require(re.search(r"(?m)^name:\s*fleet-cloud\s*$", text) is not None,
            "compose.yaml sets project name 'fleet-cloud'")
    require(":latest" not in text, "compose.yaml contains no ':latest' image tag")
    require("image: mysql:8.0.43" in text, "MySQL image pinned to mysql:8.0.43")
    require("image: traccar/traccar:6.15.3-alpine" in text,
            "Traccar image pinned to traccar/traccar:6.15.3-alpine")
    require("127.0.0.1:8082:8082" in text, "Traccar web port binds to 127.0.0.1:8082")
    return text


def check_env_example() -> None:
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    require(re.search(r"(?m)^MYSQL_PASSWORD=\S+", text) is not None,
            ".env.example declares MYSQL_PASSWORD (placeholder)")
    require(re.search(r"(?m)^MYSQL_ROOT_PASSWORD=\S+", text) is not None,
            ".env.example declares MYSQL_ROOT_PASSWORD (placeholder)")
    require("MYSQL_PASSWORD=replace-with-a-long-random-password" in text,
            ".env.example keeps a non-secret placeholder password")


def check_gitignore() -> None:
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    require(re.search(r"(?m)^\.env$", text) is not None, ".gitignore ignores .env")
    require("!.env.example" in text, ".gitignore keeps .env.example tracked")
    tracked = git_tracked_files()
    require(".env" not in tracked, "no runtime .env file is git-tracked")
    require(".env.example" in tracked, ".env.example is git-tracked")


def check_nginx() -> None:
    path = REPO_ROOT / "ops/nginx/fleet.nazimlaw.com.conf"
    text = path.read_text(encoding="utf-8")
    required = {
        "server_name fleet.nazimlaw.com;": "serves fleet.nazimlaw.com",
        "listen 443 ssl;": "listens on 443 with TLS",
        "listen 80;": "redirects plain HTTP",
        "location ^~ /.well-known/acme-challenge/": "serves ACME HTTP-01 challenges",
        "root /var/www/html;": "uses the shared ACME webroot",
        "proxy_pass http://127.0.0.1:8082;": "proxies to loopback Traccar",
        "proxy_set_header Upgrade $http_upgrade;": "supports WebSocket upgrade",
        "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;": "sets X-Forwarded-For",
        "proxy_set_header X-Forwarded-Proto https;": "sets X-Forwarded-Proto",
        "/etc/letsencrypt/live/fleet.nazimlaw.com/fullchain.pem": "uses the Let's Encrypt fullchain",
        "/etc/letsencrypt/live/fleet.nazimlaw.com/privkey.pem": "uses the Let's Encrypt private key",
        "include /etc/letsencrypt/options-ssl-nginx.conf;": "includes the host TLS options",
        "ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;": "uses the host dhparams",
    }
    for needle, label in required.items():
        require(needle in text, f"nginx template {label}")
    # The legacy shared origin certificate path must not be referenced.
    require("/etc/nginx/ssl/" not in text, "nginx template has no legacy /etc/nginx/ssl reference")
    # `map` must not collide with other included sites.
    require("$fleet_conn_upgrade" in text, "nginx template uses a namespaced upgrade variable")
    require(text.count("{") == text.count("}"), "nginx template braces are balanced")


def check_runbook_session_expectation() -> None:
    """The Session/API smoke row must document the verified Traccar 6.15.3
    unauthenticated response (HTTP 404) so the expectation cannot silently
    regress. See issue #5."""
    text = (REPO_ROOT / "docs/RUNBOOK.md").read_text(encoding="utf-8")
    row = next(
        (line for line in text.splitlines() if line.startswith("|") and "Session/API" in line),
        None,
    )
    require(row is not None, "runbook documents the Session/API smoke check")
    if row is None:
        return
    require("/api/session" in row, "runbook Session/API row targets /api/session")
    require("404" in row,
            "runbook Session/API expectation is the verified unauthenticated HTTP 404")
    require("200" not in row and "401" not in row,
            "runbook Session/API expectation no longer claims HTTP 200/401")
    require("curl -sS" in row and "-fsS" not in row,
            "runbook Session/API command uses curl -sS so a 404 is reported, not treated as failure")


def check_vendored_sources() -> None:
    """Verify the vendored upstream Traccar snapshots against their manifests.

    Delegates to ``scripts/check-vendored-sources.py`` so the integrity logic
    has a single implementation (issue #11).
    """
    spec = importlib.util.spec_from_file_location(
        "check_vendored_sources",
        Path(__file__).resolve().parent / "check-vendored-sources.py",
    )
    if spec is None or spec.loader is None:
        fail("could not load scripts/check-vendored-sources.py")
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve the module by name
    spec.loader.exec_module(module)
    problems = module.run()
    if problems:
        for problem in problems:
            fail(f"vendored sources: {problem}")
    else:
        ok(
            "vendored Traccar source snapshots match their recorded manifests "
            f"({len(module.SOURCES)} snapshots)"
        )


def check_secret_scan() -> None:
    scanned = 0
    for rel in git_tracked_files():
        path = REPO_ROOT / rel
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data:  # skip binary
            continue
        scanned += 1
        text = data.decode("utf-8", errors="replace")
        if rel == "scripts/check-deployment-artifacts.py":
            continue  # contains the pattern definitions themselves
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"secret scan: {label} found in {rel}")
    ok(f"secret scan covered {scanned} tracked text files with no matches")


def check_opencloud_static() -> None:
    text = (REPO_ROOT / "ops/opencloud/compose.yaml").read_text(encoding="utf-8")
    require(re.search(r"(?m)^name:\s*fleet-cloud-opencloud\s*$", text) is not None,
            "opencloud compose sets project name 'fleet-cloud-opencloud'")
    require(":latest" not in text, "opencloud compose contains no ':latest' image tag")
    require("opencloud-rolling" not in text,
            "opencloud compose does not use the rolling image family")
    require("image: opencloudeu/opencloud:7.2.4" in text,
            "OpenCloud image pinned to opencloudeu/opencloud:7.2.4")
    require("127.0.0.1:9200:9200" in text,
            "OpenCloud proxy port binds to 127.0.0.1:9200")
    require('files.nazimlaw.com:host-gateway' in text,
            "OpenCloud resolves its OIDC issuer through the host Nginx origin")
    require('IDM_CREATE_DEMO_USERS: "false"' in text,
            "opencloud compose disables demo users")
    require('PROXY_TLS: "false"' in text,
            "opencloud compose disables backend TLS (Nginx terminates TLS)")
    require('FRONTEND_DEFAULT_LINK_PERMISSIONS: "0"' in text,
            "opencloud compose defaults new links to internal-only")
    require('GATEWAY_STORAGE_PUBLIC_LINK_ENDPOINT: ""' in text,
            "opencloud compose disables the public-link storage endpoint")
    require('OC_SHARING_PUBLIC_SHARE_MUST_HAVE_PASSWORD: "true"' in text,
            "opencloud compose requires passwords on public links")
    require('OC_SHARING_PUBLIC_WRITEABLE_SHARE_MUST_HAVE_PASSWORD: "true"' in text,
            "opencloud compose requires passwords on writable public links")
    # The stack must never reach into the Traccar deployment or the Docker socket.
    require("/srv/fleet-cloud/" not in text,
            "opencloud compose does not reference the live Traccar tree")
    require("docker.sock" not in text, "opencloud compose does not mount the Docker socket")


def check_opencloud_env_example() -> None:
    text = (REPO_ROOT / "ops/opencloud/.env.example").read_text(encoding="utf-8")
    require("OPENCLOUD_URL=https://files.nazimlaw.com" in text,
            "opencloud .env.example sets the public files.nazimlaw.com URL")
    require(re.search(r"(?m)^OPENCLOUD_ADMIN_PASSWORD=\S+", text) is not None,
            "opencloud .env.example declares OPENCLOUD_ADMIN_PASSWORD (placeholder)")
    require("OPENCLOUD_ADMIN_PASSWORD=replace-with-a-unique-long-random-password" in text,
            "opencloud .env.example keeps a non-secret placeholder password")


def check_opencloud_nginx() -> None:
    text = (REPO_ROOT / "ops/nginx/files.nazimlaw.com.conf").read_text(encoding="utf-8")
    required = {
        "server_name files.nazimlaw.com;": "serves files.nazimlaw.com",
        "listen 443 ssl;": "listens on 443 with TLS",
        "listen 80;": "redirects plain HTTP",
        "location ^~ /.well-known/acme-challenge/": "serves ACME HTTP-01 challenges",
        "root /var/www/html;": "uses the shared ACME webroot",
        "proxy_pass http://127.0.0.1:9200;": "proxies to loopback OpenCloud",
        "client_max_body_size": "raises the upload size limit for Tus uploads",
        "proxy_buffering off;": "disables proxy buffering for SSE",
        "proxy_request_buffering off;": "disables request buffering for uploads",
        "proxy_read_timeout 3600s;": "extends the read timeout for sync",
        "proxy_send_timeout 3600s;": "extends the send timeout for sync",
        "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;": "sets X-Forwarded-For",
        "proxy_set_header X-Forwarded-Proto https;": "sets X-Forwarded-Proto",
        "/etc/letsencrypt/live/files.nazimlaw.com/fullchain.pem": "uses the Let's Encrypt fullchain",
        "/etc/letsencrypt/live/files.nazimlaw.com/privkey.pem": "uses the Let's Encrypt private key",
        "include /etc/letsencrypt/options-ssl-nginx.conf;": "includes the host TLS options",
        "ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;": "uses the host dhparams",
    }
    for needle, label in required.items():
        require(needle in text, f"opencloud nginx template {label}")
    require("/etc/nginx/ssl/" not in text,
            "opencloud nginx template has no legacy /etc/nginx/ssl reference")
    require("$opencloud_conn_upgrade" in text,
            "opencloud nginx template uses a namespaced upgrade variable")
    require(text.count("{") == text.count("}"),
            "opencloud nginx template braces are balanced")


def check_opencloud_runbook() -> None:
    text = (REPO_ROOT / "docs/RUNBOOK-opencloud.md").read_text(encoding="utf-8")
    required = {
        "Can edit": "documents the Birand 'Can edit' Space role",
        "Can manage": "documents the Ulaş 'Can manage' Space role",
        "Fleet Cloud": "names the Fleet Cloud Space",
        "export-shareable-files.sh": "covers the secrets-free repository export",
        "status.php": "documents the health endpoint",
        "docker volume rm fleet-cloud-opencloud-config": "covers data removal/revocation",
        "certbot certonly": "covers the TLS bootstrap",
        "http://127.0.0.1:9200": "documents the loopback upstream",
    }
    for needle, label in required.items():
        require(needle in text, f"opencloud runbook {label}")


def _env_map(service: dict) -> dict:
    env = service.get("environment") or {}
    if isinstance(env, dict):
        return {str(k): ("" if v is None else str(v)) for k, v in env.items()}
    out = {}
    for item in env:
        key, _, value = str(item).partition("=")
        out[key] = value
    return out


def check_opencloud_compose_json(compose_json_path: str) -> None:
    try:
        data = json.loads(Path(compose_json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not load resolved opencloud compose JSON: {exc}")
        return

    require(data.get("name") == "fleet-cloud-opencloud",
            "resolved opencloud project name is fleet-cloud-opencloud")
    services = data.get("services", {})
    require(set(services) == {"opencloud"},
            "resolved opencloud services are exactly opencloud")

    svc = services.get("opencloud", {})
    image = svc.get("image", "")
    require(bool(image) and not image.endswith(":latest") and "rolling" not in image,
            f"opencloud image is pinned and non-floating ({image or 'missing'})")
    require(svc.get("restart") == "unless-stopped", "opencloud restart policy is unless-stopped")
    require(bool(svc.get("healthcheck")), "opencloud has a healthcheck")
    limits = svc.get("deploy", {}).get("resources", {}).get("limits", {})
    require(bool(limits.get("cpus")) and bool(limits.get("memory")),
            "opencloud has CPU and memory limits")
    require("internal" in (svc.get("networks") or {}),
            "opencloud is attached to the dedicated network")

    # Only the proxy port, on host loopback, may be published.
    ports = svc.get("ports", []) or []
    published = [(p.get("host_ip"), p.get("published"), p.get("target")) for p in ports]
    require(len(published) == 1, "opencloud publishes exactly one port")
    require(all(ip == "127.0.0.1" for ip, *_ in published),
            "opencloud published ports bind to 127.0.0.1 only")
    require(any(str(target) == "9200" for _, _, target in published),
            "opencloud publishes the proxy port 9200")

    extra_hosts = svc.get("extra_hosts") or []
    if isinstance(extra_hosts, dict):
        extra_hosts = [f"{key}={value}" for key, value in extra_hosts.items()]
    normalized_hosts = {str(item).replace(":", "=", 1) for item in extra_hosts}
    require(normalized_hosts == {"files.nazimlaw.com=host-gateway"},
            "opencloud has exactly the OIDC issuer host-gateway mapping")

    mounts = svc.get("volumes", []) or []
    targets = {m.get("target") for m in mounts}
    require("/etc/opencloud" in targets, "opencloud config volume mounted")
    require("/var/lib/opencloud" in targets, "opencloud data volume mounted")
    require(not any("/srv/fleet-cloud" in str(m.get("source", "")) for m in mounts),
            "opencloud mounts no Traccar host path")

    volumes = data.get("volumes", {}) or {}
    volume_names = {v.get("name") for v in volumes.values()}
    for expected in ("fleet-cloud-opencloud-config", "fleet-cloud-opencloud-data"):
        require(expected in volume_names, f"named volume present: {expected}")

    networks = data.get("networks", {}) or {}
    require("fleet-cloud-opencloud-net" in {n.get("name") for n in networks.values()},
            "dedicated network fleet-cloud-opencloud-net present")

    env = _env_map(svc)
    require(env.get("IDM_CREATE_DEMO_USERS") in ("false", "False", "0"),
            "resolved opencloud disables demo users")
    require(env.get("PROXY_TLS") in ("false", "False", "0"),
            "resolved opencloud disables backend TLS")
    require(env.get("PROXY_ENABLE_BASIC_AUTH") in ("false", "False", "0"),
            "resolved opencloud disables WebDAV basic auth")
    require(env.get("FRONTEND_DEFAULT_LINK_PERMISSIONS") == "0",
            "resolved opencloud defaults links to internal-only")
    require(env.get("GATEWAY_STORAGE_PUBLIC_LINK_ENDPOINT") == "",
            "resolved opencloud disables the public-link storage endpoint")
    require(env.get("OC_SHARING_PUBLIC_SHARE_MUST_HAVE_PASSWORD") in ("true", "True", "1"),
            "resolved opencloud requires public-link passwords")
    require(env.get("OC_SHARING_PUBLIC_WRITEABLE_SHARE_MUST_HAVE_PASSWORD") in ("true", "True", "1"),
            "resolved opencloud requires passwords on writable public links")
    require(env.get("OC_URL", "").startswith("https://files.nazimlaw.com"),
            "resolved opencloud public URL is https://files.nazimlaw.com")
    ok("resolved OpenCloud Compose configuration validated")


def check_compose_json(compose_json_path: str) -> None:
    try:
        data = json.loads(Path(compose_json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not load resolved compose JSON: {exc}")
        return

    require(data.get("name") == "fleet-cloud", "resolved project name is fleet-cloud")
    services = data.get("services", {})
    require(set(services) == {"database", "traccar"},
            "resolved services are exactly database and traccar")

    def image_of(name: str) -> str:
        return services.get(name, {}).get("image", "")

    for name in ("database", "traccar"):
        image = image_of(name)
        require(bool(image) and not image.endswith(":latest"),
                f"{name} image is pinned and not :latest ({image or 'missing'})")
        svc = services.get(name, {})
        require(svc.get("restart") == "unless-stopped", f"{name} restart policy is unless-stopped")
        require(bool(svc.get("healthcheck")), f"{name} has a healthcheck")
        limits = svc.get("deploy", {}).get("resources", {}).get("limits", {})
        require(bool(limits.get("cpus")) and bool(limits.get("memory")),
                f"{name} has CPU and memory limits")
        require("internal" in (svc.get("networks") or {}),
                f"{name} is attached to the dedicated network")

    # Database must not be published at all.
    require(not services.get("database", {}).get("ports"),
            "database publishes no host port")

    # Traccar web must publish only on host loopback.
    ports = services.get("traccar", {}).get("ports", []) or []
    published = [(p.get("host_ip"), p.get("published"), p.get("target"), p.get("protocol")) for p in ports]
    require(len(published) == 1, "traccar publishes exactly one port")
    require(all(ip == "127.0.0.1" for ip, *_ in published),
            "traccar published ports bind to 127.0.0.1 only")
    require(any(str(target) == "8082" for _, _, target, _ in published),
            "traccar publishes web port 8082")
    for _, pubbed, target, _ in published:
        try:
            value = int(pubbed)
        except (TypeError, ValueError):
            value = int(target)
        if value in TRACKER_PORT_RANGE:
            fail(f"tracker protocol port {value} is published (must not be by default)")
    require(not any(int(t) in TRACKER_PORT_RANGE for _, _, t, _ in published),
            "no tracker protocol port (5000-5300) is published")

    # Traccar depends on a healthy database.
    depends = services.get("traccar", {}).get("depends_on", {}) or {}
    db_dep = depends.get("database", {}) if isinstance(depends, dict) else {}
    require(db_dep.get("condition") == "service_healthy",
            "traccar waits for a healthy database")

    # Traccar persistent data and logs.
    mounts = services.get("traccar", {}).get("volumes", []) or []
    targets = {m.get("target") for m in mounts}
    require("/opt/traccar/data" in targets, "traccar data volume mounted")
    require("/opt/traccar/logs" in targets, "traccar logs volume mounted")
    db_targets = {m.get("target") for m in (services.get("database", {}).get("volumes", []) or [])}
    require("/var/lib/mysql" in db_targets, "database data volume mounted")

    # Named volumes.
    volumes = data.get("volumes", {}) or {}
    names = {v.get("name") for v in volumes.values()}
    for expected in ("fleet-cloud-db-data", "fleet-cloud-traccar-data",
                     "fleet-cloud-traccar-logs"):
        require(expected in names, f"named volume present: {expected}")

    # Dedicated network with loopback default binding.
    networks = data.get("networks", {}) or {}
    require("fleet-cloud-net" in {n.get("name") for n in networks.values()},
            "dedicated network fleet-cloud-net present")
    ok("resolved Compose configuration validated")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose-json", help="resolved `docker compose config --format json` output")
    parser.add_argument("--opencloud-compose-json",
                        help="resolved `docker compose config --format json` output for the OpenCloud stack")
    args = parser.parse_args()

    check_required_files()
    check_compose_static()
    check_env_example()
    check_gitignore()
    check_nginx()
    check_runbook_session_expectation()
    check_opencloud_static()
    check_opencloud_env_example()
    check_opencloud_nginx()
    check_opencloud_runbook()
    check_vendored_sources()
    check_secret_scan()
    if args.compose_json:
        check_compose_json(args.compose_json)
    if args.opencloud_compose_json:
        check_opencloud_compose_json(args.opencloud_compose_json)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed out of {checks}.")
        return 1
    print(f"All {checks} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
