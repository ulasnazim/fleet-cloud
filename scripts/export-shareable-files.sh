#!/usr/bin/env bash
# Produce a secrets-free export of the repository for sharing in the OpenCloud
# `Fleet Cloud` Space (issue #7).
#
# Only git-tracked files are exported, so deployment-only files (.env, runtime
# data, logs) can never be included: they are gitignored and never tracked.
# The live /srv/fleet-cloud deployment tree is NOT read or synced.
#
# Usage: scripts/export-shareable-files.sh [revision] [output.tar.gz]
#   revision     git revision to export (default: HEAD)
#   output       output path (default: fleet-cloud-share-export.tar.gz)
#
# The archive contains no credentials. Review it with `tar tzf` before upload.
set -euo pipefail

rev="${1:-HEAD}"
out="${2:-fleet-cloud-share-export.tar.gz}"

cd "$(git rev-parse --show-toplevel)"

# Refuse to export if a runtime secret file is ever tracked.
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "refusing: .env is git-tracked; remove it from the index first" >&2
    exit 1
fi

git archive --format=tar.gz -o "$out" "$rev"

echo "wrote ${out} from ${rev} (tracked files only; no secrets)"
echo "review before upload: tar tzf ${out} | grep -E '(^|/)\\.env$' && echo 'unexpected secret' || true"
