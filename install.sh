#!/bin/sh
set -e

REPO_URL="https://github.com/Abragus/syncsmith"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null | grep -q "$REPO_URL"; then
    IN_REPO=true
else
    IN_REPO=false
fi

NO_APPLY=false
for arg in "$@"; do
    case "$arg" in
        --no-apply)
            NO_APPLY=true
            shift
            ;;
    esac
done


# --- Prerequisites -----------------------------------------------------------
need_pkg() {
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            MISSING="$MISSING $cmd"
        fi
    done
}

need_pkg git python3

if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi


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
else
    echo "[syncsmith] All required packages already installed."
fi
# ---------------------------------------------------------------------------

# Clone or update repository
# Check if we're already in a syncsmith repo
if [ "$IN_REPO" = true ]; then
    echo "[syncsmith] Detected install in current directory, skipping cloning."
    INSTALL_DIR="$SCRIPT_DIR"
    git -C "$INSTALL_DIR" pull
    echo "[syncsmith] Ready."
else
    INSTALL_DIR="${INSTALL_DIR:-/opt/syncsmith}"
    echo "[syncsmith] Installing into $INSTALL_DIR..."
    
    # Check if install directory exists and is non-empty
    if [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR")" ]; then
        echo "[syncsmith] WARNING: $INSTALL_DIR already exists and is not empty."
        read -p "[syncsmith] Overwrite contents? [y/N]: " CONFIRM
        case "$CONFIRM" in
            y|Y)
                ${SUDO} rm -rf "$INSTALL_DIR"
                ;;
            *)
                echo "[syncsmith] Aborting installation."
                exit 1
                ;;
        esac
    fi

    ${SUDO} mkdir -p "$INSTALL_DIR"
    ${SUDO} chown "$USER":"$USER" "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
    echo "[syncsmith] Installed to $INSTALL_DIR."
fi

#  Add systemd service if available
if command -v systemctl >/dev/null 2>&1; then
    echo "[syncsmith] Installing systemd service..."

    if [ "$IN_REPO" = true ]; then
        echo "[syncsmith] Creating symlink in /opt/syncsmith for portable install..."
        ${SUDO} mkdir -p /opt/syncsmith
        ln -s "$INSTALL_DIR/syncsmith.sh" /opt/syncsmith/syncsmith.sh
    fi


    ${SUDO} cp "$INSTALL_DIR/scripts/syncsmith.service" /etc/systemd/system/syncsmith.service
    ${SUDO} cp "$INSTALL_DIR/scripts/syncsmith.timer"   /etc/systemd/system/syncsmith.timer

    ${SUDO} systemctl daemon-reload
    ${SUDO} systemctl enable --now syncsmith.timer

    echo "[syncsmith] Systemd timer installed and enabled (runs nightly at 03:00)"
else
    echo "[syncsmith] Systemd not available — automatic syncing disabled."
fi

# Run syncsmith once to apply settings
RUNFILE="$INSTALL_DIR/syncsmith.sh"
chmod +x "$RUNFILE"

if [ "$NO_APPLY" = false ]; then
    echo "[syncsmith] Applying settings now..."
    "$RUNFILE"
else
    echo "[syncsmith] Exiting without applying settings."
fi