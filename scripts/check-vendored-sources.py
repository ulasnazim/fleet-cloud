#!/usr/bin/env python3
"""Deterministic integrity checks for the vendored upstream Traccar source.

The repository vendors two unmodified upstream source snapshots under
``vendor/`` so GitHub can browse them directly instead of following a submodule
(issue #11):

  * ``vendor/traccar-server`` <- https://github.com/traccar/traccar
  * ``vendor/traccar-web``    <- https://github.com/traccar/traccar-web

Each snapshot ships with a committed ``*.sha256`` manifest that lists the
sha256 of every regular file, sorted by path in byte order (the C locale), in
the same format as ``sha256sum`` output. This script rebuilds that manifest
from the working tree and compares it byte-for-byte with the committed
manifest, so any added, removed or modified vendored file fails the check. It
also confirms each upstream license file is intact.

Run: ``python3 scripts/check-vendored-sources.py``
Exit code 0 means every vendored snapshot matches its recorded manifest.

No network access is required. The snapshots are reference source only: they
are never built and never affect the running deployment, which uses the pinned
``traccar/traccar:6.15.3-alpine`` image.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Source:
    name: str
    directory: str  # relative to REPO_ROOT
    manifest: str  # relative to REPO_ROOT
    repository: str
    tag: str
    commit: str
    license_file: str  # relative to the source directory
    license_needle: str


SOURCES = (
    Source(
        name="traccar-server",
        directory="vendor/traccar-server",
        manifest="vendor/traccar-server.sha256",
        repository="https://github.com/traccar/traccar",
        tag="v6.15.3",
        commit="5eb957893c22b988f831200e976b36262d2b8592",
        license_file="LICENSE.txt",
        license_needle="Apache License",
    ),
    Source(
        name="traccar-web",
        directory="vendor/traccar-web",
        manifest="vendor/traccar-web.sha256",
        repository="https://github.com/traccar/traccar-web",
        tag="v6.15.3",
        commit="cfedd3415415623ddbeb74ed6fe6238f3f7a47e0",
        license_file="LICENSE.txt",
        license_needle="Apache License",
    ),
)


def build_manifest(source_dir: Path) -> bytes:
    """Return the canonical manifest bytes for a source directory.

    The format matches ``sha256sum`` output (``<hex>  <relative-path>``), one
    line per regular file, sorted by path in byte order (the C locale).
    """
    paths = [
        p.relative_to(source_dir).as_posix()
        for p in source_dir.rglob("*")
        if p.is_file() and not p.is_symlink()
    ]
    paths.sort(key=lambda value: value.encode("utf-8"))
    lines = []
    for rel in paths:
        digest = hashlib.sha256((source_dir / rel).read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}\n")
    return "".join(lines).encode("utf-8")


def parse_manifest(data: bytes) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        digest, sep, rel = line.partition("  ")
        if not sep or len(digest) != 64:
            continue
        entries[rel] = digest
    return entries


def check_source(source: Source) -> list[str]:
    problems: list[str] = []
    source_dir = REPO_ROOT / source.directory
    manifest_path = REPO_ROOT / source.manifest

    if not source_dir.is_dir():
        return [f"{source.name}: missing vendored directory {source.directory}"]
    if not manifest_path.is_file():
        return [f"{source.name}: missing manifest {source.manifest}"]

    committed = manifest_path.read_bytes()
    rebuilt = build_manifest(source_dir)

    if rebuilt == committed:
        entries = parse_manifest(committed)
        print(
            f"PASS: {source.name} matches {source.manifest} "
            f"({len(entries)} files, {source.repository} {source.tag})"
        )
    else:
        want = parse_manifest(committed)
        got = parse_manifest(rebuilt)
        missing = sorted(set(want) - set(got))
        added = sorted(set(got) - set(want))
        changed = sorted(rel for rel in set(want) & set(got) if want[rel] != got[rel])
        for rel in missing:
            problems.append(f"{source.name}: vendored file missing: {rel}")
        for rel in added:
            problems.append(f"{source.name}: unexpected vendored file: {rel}")
        for rel in changed:
            problems.append(f"{source.name}: vendored file changed: {rel}")
        if not (missing or added or changed):
            problems.append(
                f"{source.name}: manifest bytes differ from {source.manifest} "
                "without a per-file difference (check ordering or line endings)"
            )
        for problem in problems:
            print(f"FAIL: {problem}")

    license_path = source_dir / source.license_file
    if not license_path.is_file():
        problem = f"{source.name}: missing upstream license {source.license_file}"
        problems.append(problem)
        print(f"FAIL: {problem}")
    else:
        text = license_path.read_text(encoding="utf-8", errors="replace")
        if source.license_needle not in text:
            problem = (
                f"{source.name}: {source.license_file} does not contain "
                f"{source.license_needle!r}"
            )
            problems.append(problem)
            print(f"FAIL: {problem}")
        else:
            print(f"PASS: {source.name} preserves upstream {source.license_file}")

    return problems


def run() -> list[str]:
    """Verify every vendored snapshot; return a list of problem messages."""
    problems: list[str] = []
    for source in SOURCES:
        problems.extend(check_source(source))
    return problems


def main() -> int:
    problems = run()
    print()
    if problems:
        print(f"{len(problems)} vendored-source check(s) failed.")
        return 1
    print(f"All {len(SOURCES)} vendored source snapshot(s) verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())