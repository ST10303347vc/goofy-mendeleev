#!/bin/bash
set -euo pipefail

root=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
mkdir -p .build

python=${GOOFY_PYTHON:-python3}
if ! python_path=$("$python" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or later required"; print(sys.executable)'); then
    printf '%s\n' 'Install Python 3.10+ or set GOOFY_PYTHON to its executable.' >&2
    exit 1
fi
python_key=$({ printf '%s\n' "$python_path"; "$python_path" --version; cat requirements.txt; } | shasum -a 256)
if [[ ! -d .build/vendor || ! -f .build/python.stamp || $(cat .build/python.stamp) != "$python_key" ]]; then
    stage=$(mktemp -d "$root/.build/python.XXXXXX")
    trap 'rm -rf "$stage"' EXIT
    "$python_path" -m venv "$stage/env"
    "$stage/env/bin/python" -m pip --disable-pip-version-check install --quiet --no-compile --target "$stage/vendor" -r requirements.txt
    rm -rf .build/vendor
    mv "$stage/vendor" .build/vendor
    printf '%s\n' "$python_key" > .build/python.stamp
fi
printf '%s\n' "$python_path" > .build/python-path

# The terminal launcher can import a database without rebuilding the UI.
if [[ ${1:-} == --python-only ]]; then exit 0; fi

assets=frontend/assets
if [[ ! -f "$assets/tailwind.css" || ! -f "$assets/vue.js" || ! -f "$assets/icons.css" || ! -f "$assets/fonts.css" ||
      ! -f "$assets/Phosphor-Light.woff2" || ! -f "$assets/Phosphor-Thin.woff2" ||
      package-lock.json -nt "$assets/tailwind.css" || scripts/build-frontend.mjs -nt "$assets/tailwind.css" ||
      scripts/tailwind.config.cjs -nt "$assets/tailwind.css" || frontend/index.html -nt "$assets/tailwind.css" ||
      frontend/app.js -nt "$assets/tailwind.css" ]]; then
    if ! command -v npm >/dev/null; then
        printf '%s\n' 'Install Node.js with npm to build the browser assets.' >&2
        exit 1
    fi
    if [[ ! -d node_modules || ! -f .build/npm.stamp || package-lock.json -nt .build/npm.stamp ]]; then
        npm ci --ignore-scripts --no-fund --no-audit
        touch .build/npm.stamp
    fi
    npm run build
fi
