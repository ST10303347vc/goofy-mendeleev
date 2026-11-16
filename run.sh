#!/bin/bash
set -euo pipefail

root=$(cd -- "$(dirname -- "$0")" && pwd)
cd "$root"

if [[ ${1:-} == --import-legacy ]]; then
    ./scripts/setup-local.sh --python-only
else
    ./scripts/setup-local.sh
fi

export PYTHONPATH="$root/.build/vendor"
export PYTHONDONTWRITEBYTECODE=1
exec "$(cat .build/python-path)" -m backend.server "$@"
