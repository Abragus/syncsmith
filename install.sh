#!/bin/sh
set -e

REPO_URL="https://github.com/Abragus/syncsmith"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

YES_FLAG=false
AUTO_MODE=false
for arg in "$@"; do
    case "$arg" in
        -y|--yes)
            YES_FLAG=true
            ;;
        --auto)
            AUTO_MODE=true
            ;;
    esac
done

confirm() {
    prompt_msg="$1"
    info_msg="$2"
    default="$3"

    # Build prompt suffix
    if [ "$default" = "y" ]; then
        suffix="[Y/n]"
    else
        suffix="[y/N]"
    fi

    # Auto-confirm path: show info_msg and return success
    if [ "$YES_FLAG" = "true" ] && [ "$default" != "N" ]; then
        [ -n "$info_msg" ] && printf "%s\n" "[syncsmith] $info_msg"
        return 0
    fi

    if [ "$AUTO_MODE" = "true" ]; then
        answer="$default"
    else
        # Show the prompt
        printf "%s %s " "[syncsmith] $prompt_msg" "$suffix"

        # Interactive read
        if ! read -r answer < /dev/tty; then
            # EOF or read failure — treat as decline
            printf "\n"
            return 1
        fi
    fi

    # Normalize empty -> default
    if [ -z "$answer" ]; then
        answer="$default"
    fi

    case "$answer" in
        Y|y|Y*|y*)
            [ -n "$info_msg" ] && printf "%s\n" "[syncsmith] $info_msg"
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}


echo "[syncsmith] This script will install SyncSmith on your system."
if ! confirm "Continue with installation?" "Starting installation..." "y"; then
    echo "[syncsmith] Aborting installation."
    exit 0
fi

# --- Prerequisites -----------------------------------------------------------
need_pkg() {
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            MISSING="$MISSING $cmd"
        fi
    done
}

need_pkg git python3 python3-pip python3-venv

if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi


if [ -n "$MISSING" ]; then
    echo "[syncsmith] Missing required packages:$MISSING"
    if ! confirm "Attempt automatic dependency installation?" "Attempting automatic dependency installation..." "y"; then
        echo "[syncsmith] Aborting installation. Please install the missing packages manually."
        exit 1
    fi
    echo "[syncsmith] Attempting to detect package manager..."

    if command -v apt-get >/dev/null 2>&1; then
        echo "[syncsmith] Installing via apt..."
        ${SUDO} apt-get update -qq
        ${SUDO} apt-get install -y ${MISSING}
    elif command -v dnf >/dev/null 2>&1; then
        echo "[syncsmith] Installing via dnf..."
        ${SUDO} dnf install -y git python3 python3-pip python3-virtualenv
    elif command -v yum >/dev/null 2>&1; then
        echo "[syncsmith] Installing via yum..."
        ${SUDO} yum install -y ${MISSING}
    elif command -v pacman >/dev/null 2>&1; then
        echo "[syncsmith] Installing via pacman..."
        ${SUDO} pacman -Sy --noconfirm git python
    elif command -v zypper >/dev/null 2>&1; then
        echo "[syncsmith] Installing via zypper..."
        ${SUDO} zypper --non-interactive install ${MISSING}
    elif command -v apk >/dev/null 2>&1; then
        echo "[syncsmith] Installing via apk..."
        ${SUDO} apk add ${MISSING}
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
if git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null | grep -q "$REPO_URL"; then
    IN_REPO=true
else
    IN_REPO=false
fi

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
        
        if confirm "Overwrite contents?" "" "N"; then
            echo "[syncsmith] Removing existing contents of $INSTALL_DIR..."
            ${SUDO} rm -rf "$INSTALL_DIR"
        else
            echo "[syncsmith] Aborting installation."
            exit 1
        fi
    fi

    ${SUDO} mkdir -p "$INSTALL_DIR"
    ${SUDO} chown "$USER":"$USER" "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
    echo "[syncsmith] Installed to $INSTALL_DIR."
fi

if [ "$IN_REPO" = true ] && [ "$INSTALL_DIR" != "/opt/syncsmith" ] && ! [ -d "/opt/syncsmith/.git" ]; then
    echo "[syncsmith] Creating symlink in /opt/syncsmith for portable install..."
    ${SUDO} mkdir -p /opt/syncsmith
    ln -s "$INSTALL_DIR/syncsmith.sh" /opt/syncsmith/syncsmith.sh
fi

# ---------------------------------------------------------------------------
# Create Python virtual environment
VENV_DIR="$INSTALL_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[syncsmith] Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "[syncsmith] Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# ---------------------------------------------------------------------------
# Run syncsmith once to apply settings

RUNFILE="$INSTALL_DIR/syncsmith.sh"
chmod +x "$RUNFILE"

if confirm "Run syncsmith now to apply settings?" "Running syncsmith now..." "y"; then
    echo "[syncsmith] Running syncsmith..."
    "$RUNFILE" "$@" "--user" "$USER"
else
    echo "[syncsmith] Installation complete. You can run syncsmith later via:"
    echo "  $RUNFILE"
    exit 0
fi
