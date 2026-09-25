# Vendored upstream Traccar source

This directory contains **unmodified snapshots of the official Traccar source**
so that the product source can be browsed directly on GitHub (issue #11). The
files are normal, tracked repository files — there are **no git submodules**.

These snapshots are **reference source only**. They are never built and never
affect the running deployment, which continues to use the pinned
`traccar/traccar:6.15.3-alpine` image described in `compose.yaml`.

## Snapshots

| Directory | Upstream repository | Tag | Commit (immutable) | License | Files | Manifest |
|---|---|---|---|---|---|---|
| `vendor/traccar-server/` | https://github.com/traccar/traccar | `v6.15.3` | `5eb957893c22b988f831200e976b36262d2b8592` | Apache-2.0 (`LICENSE.txt`) | 1841 | `vendor/traccar-server.sha256` |
| `vendor/traccar-web/` | https://github.com/traccar/traccar-web | `v6.15.3` | `cfedd3415415623ddbeb74ed6fe6238f3f7a47e0` | Apache-2.0 (`LICENSE.txt`) | 277 | `vendor/traccar-web.sha256` |

Server release: <https://github.com/traccar/traccar/releases/tag/v6.15.3>
(web ships as a tag without a GitHub release).

Manifest digests (sha256 of the committed manifest file itself):

```
c58a172aa340589fa7c8d6f765b6d6dd39532d2b0945338824c1c23a20c32678  vendor/traccar-server.sha256
f83e9f2d209fab045b6ac12fe22bfd9813821e8bb29e7462f6b6c6623f6eec08  vendor/traccar-web.sha256
```

## Provenance and how the snapshots were produced

Each snapshot is the exact set of files-tracked-at-the-tag, obtained from the
GitHub source archive for the immutable commit above:

```sh
curl -sSL -o traccar-server.tar.gz \
  https://codeload.github.com/traccar/traccar/tar.gz/5eb957893c22b988f831200e976b36262d2b8592
curl -sSL -o traccar-web.tar.gz \
  https://codeload.github.com/traccar/traccar-web/tar.gz/cfedd3415415623ddbeb74ed6fe6238f3f7a47e0
tar -xzf traccar-server.tar.gz -C vendor/traccar-server --strip-components=1
tar -xzf traccar-web.tar.gz    -C vendor/traccar-web    --strip-components=1
```

File contents, names and executable bits are preserved byte-for-byte.

## Documented exclusions

The snapshots match the upstream tag except for these explicitly documented,
non-content exclusions:

- **Upstream `.git` metadata** is not imported (the source archive never
  contains it), by issue requirement.
- **`vendor/traccar-server/traccar-web/` (upstream submodule)** — the server
  repo declares `traccar-web` as a git submodule in `.gitmodules`. A source
  archive cannot include submodule content, so that directory is empty and is
  not present here. Submodules are forbidden by issue #11; the web client
  source is instead provided in full at `vendor/traccar-web/`.

Nothing else is excluded: no source file, license or notice was removed.

## Integrity verification

`scripts/check-vendored-sources.py` rebuilds each manifest from the working
tree and compares it byte-for-byte with the committed manifest, then confirms
the Apache-2.0 license files are intact. Any added, removed or modified
vendored file fails the check. It is wired into
`scripts/check-deployment-artifacts.py`, so the standard repository check
covers it:

```sh
python3 scripts/check-vendored-sources.py
python3 scripts/check-deployment-artifacts.py
```

## Refreshing to a newer upstream version

Do this only for a deliberate upgrade issue, and update the pinned image tag in
`compose.yaml` in the same change:

1. Resolve the immutable commit for the new tag:

   ```sh
   gh api repos/traccar/traccar/git/ref/tags/vX.Y.Z --jq .object.sha
   gh api repos/traccar/traccar-web/git/ref/tags/vX.Y.Z --jq .object.sha
   ```

2. Replace the snapshot with the archive for that commit (same commands as
   above, using the new SHA), deleting the old directory contents first so
   removed files do not linger.

3. Regenerate the manifests (path order is the C locale; format is
   `sha256sum`):

   ```sh
   cd vendor/traccar-server && LC_ALL=C find . -type f -printf '%P\0' \
     | LC_ALL=C sort -z | xargs -0 sha256sum > ../traccar-server.sha256
   cd ../traccar-web && LC_ALL=C find . -type f -printf '%P\0' \
     | LC_ALL=C sort -z | xargs -0 sha256sum > ../traccar-web.sha256
   ```

4. Update the table, digests and commit SHAs in this file, and the `SOURCES`
   records in `scripts/check-vendored-sources.py`.

5. Run `python3 scripts/check-deployment-artifacts.py` and the CI checks; open
   a pull request.

## Licensing

Both snapshots are Apache-2.0 (see each `LICENSE.txt`). Traccar is used as an
unmodified upstream dependency under the owner-approved decision in
`docs/adr/0002-traccar-deployment-foundation.md`; the license and attribution
files are preserved verbatim. No credentials, runtime data, build outputs or
production artifacts are imported.