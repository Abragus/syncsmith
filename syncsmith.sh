#!/bin/sh
PY=python3
if [ -f "$(dirname "$0")/syncsmith.py" ]; then
    INSTALL_DIR="$(dirname "$0")"
else
    INSTALL_DIR="${INSTALL_DIR:-/opt/syncsmith}"
fi

cd "$INSTALL_DIR" || { echo "[syncsmith] Failed to enter install directory"; exit 1; }
$PY syncsmith.py "$@"
