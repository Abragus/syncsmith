#!/bin/sh
PY=python3
INSTALL_DIR="${INSTALL_DIR:-/opt/syncsmith}"
cd "$INSTALL_DIR" || { echo "[syncsmith] Failed to enter install directory"; exit 1; }
$PY syncsmith.py "$@"
