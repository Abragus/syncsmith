#!/bin/sh
PY=python3
if [ -f "$(dirname "$0")/syncsmith.py" ]; then
    INSTALL_DIR="$(dirname "$0")"
else
    INSTALL_DIR="${INSTALL_DIR:-/opt/syncsmith}"
fi

AUTO_MODE=false
REPAIR=false
REPAIR_ATTEMPTED=false
for arg in "$@"; do
    case "$arg" in
        --auto)
            AUTO_MODE=true
            ;;
        --repair)
            REPAIR=true
            ;;
        --repair-attempted)
            REPAIR_ATTEMPTED=true
            ;;
    esac
done

cd "$INSTALL_DIR" || { echo "[syncsmith] Failed to enter install directory"; exit 1; }

if [ "$AUTO_MODE" = true ]; then
    git stash -u
    git pull -f origin main
else
    git pull origin main
fi

$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/syncsmith.py "$@"

if ! [ "$REPAIR_ATTEMPTED" = true ] && { [ $? -ne 0 ] && [ "$AUTO_MODE" = true ]; } || [ "$REPAIR" = true ]; then
    echo "Running automatic repair..."
    sudo /opt/syncsmith/install.sh --auto --repair-attempted
fi