#!/bin/bash
set -euo pipefail

root=$(cd -- "$(dirname -- "$0")" && pwd)
cd "$root"
if [[ $(uname -s) != Darwin ]]; then
    printf '%s\n' 'The desktop installer requires macOS.' >&2
    exit 1
fi
if ! xcrun --find swiftc >/dev/null; then
    printf '%s\n' 'Install the Xcode Command Line Tools (xcode-select --install), then rerun this script.' >&2
    exit 1
fi
if [[ ${1:-} == --build-only && $# -eq 1 ]]; then
    destination="$root/.build/restored"
elif [[ $# -eq 0 ]]; then
    destination="$HOME/Applications"
else
    printf 'Usage: %s [--build-only]\n' "$0" >&2
    exit 2
fi
./scripts/setup-local.sh
mkdir -p "$destination"
stage=$(mktemp -d "$destination/.goofy-mendeleev.XXXXXX")
app="$destination/Goofy Mendeleev.app"
bundle="$stage/Goofy Mendeleev.app"
cleanup() {
    if [[ -e "$stage/Previous.app" && ! -e "$app" ]]; then
        mv "$stage/Previous.app" "$app"
    fi
    rm -rf "$stage"
}
trap cleanup EXIT
contents="$bundle/Contents"
resources="$contents/Resources"
mkdir -p "$contents/MacOS" "$resources/backend" "$resources/frontend"
cp macos/Info.plist "$contents/Info.plist"
/usr/bin/plutil -insert GoofyPythonPath -string "$(cat .build/python-path)" "$contents/Info.plist"
cp backend/*.py "$resources/backend/"
cp frontend/index.html frontend/app.js frontend/styles.css "$resources/frontend/"
cp -R frontend/assets "$resources/frontend/assets"
cp -R .build/vendor "$resources/vendor"
MACOSX_DEPLOYMENT_TARGET=13.0 xcrun swiftc -O macos/main.swift macos/LockedDisplay.swift -o "$contents/MacOS/Goofy Mendeleev"
/usr/bin/codesign --force --sign - "$bundle"
/usr/bin/codesign --verify --strict "$bundle"
if [[ -e "$app" ]]; then
    if [[ $(/usr/bin/plutil -extract CFBundleIdentifier raw "$app/Contents/Info.plist" 2>/dev/null) != local.goofy-mendeleev.app ]]; then
        printf 'An unrelated app already exists at %s.\n' "$app" >&2
        exit 1
    fi
    mv "$app" "$stage/Previous.app"
fi
mv "$bundle" "$app"
printf 'Goofy Mendeleev is ready at: %s\n' "$app"
