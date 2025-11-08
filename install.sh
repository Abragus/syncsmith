#!/bin/sh
set -e
REPO_URL="https://github.com/yourusername/syncsmith.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/syncsmith}"

echo "[syncsmith] Installing into $INSTALL_DIR..."

# --- Prerequisites -----------------------------------------------------------
need_pkg() {
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            MISSING="$MISSING $cmd"
        fi
    done
}

need_pkg git python3

if command -v sudo &> /dev/null; then
    SUDO="sudo"

if [ -n "$MISSING" ]; then
    echo "[syncsmith] Missing required packages:$MISSING"
    echo "[syncsmith] Attempting to detect package manager..."

    if command -v apt-get >/dev/null 2>&1; then
        echo "[syncsmith] Installing via apt..."
        ${SUDO} apt-get update -qq
        ${SUDO} apt-get install -y git python3
    elif command -v dnf >/dev/null 2>&1; then
        echo "[syncsmith] Installing via dnf..."
        ${SUDO} dnf install -y git python3
    elif command -v yum >/dev/null 2>&1; then
        echo "[syncsmith] Installing via yum..."
        ${SUDO} yum install -y git python3
    elif command -v pacman >/dev/null 2>&1; then
        echo "[syncsmith] Installing via pacman..."
        ${SUDO} pacman -Sy --noconfirm git python
    elif command -v zypper >/dev/null 2>&1; then
        echo "[syncsmith] Installing via zypper..."
        ${SUDO} zypper --non-interactive install git python3
    elif command -v apk >/dev/null 2>&1; then
        echo "[syncsmith] Installing via apk..."
        ${SUDO} apk add git python3
    else
        echo "[syncsmith] Could not detect a known package manager."
        echo "Please install the following packages manually:$MISSING"
        exit 1
    fi
fi
# ---------------------------------------------------------------------------


# Clone or update
if [ ! -d "$INSTALL_DIR/.git" ]; then
  sudo mkdir -p "$INSTALL_DIR"
  sudo chown "$USER":"$USER" "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
else
  git -C "$INSTALL_DIR" pull
fi

cd "$INSTALL_DIR"
chmod +x runner.sh
echo "[syncsmith] Ready. Run: sudo $INSTALL_DIR/runner.sh --apply"
