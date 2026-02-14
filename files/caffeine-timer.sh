#!/bin/bash

# Configuration
SCHEMA_DIR="$HOME/.local/share/gnome-shell/extensions/caffeine@patapon.info/schemas/"
KEY="org.gnome.shell.extensions.caffeine"
PID_FILE="/tmp/caffeine_timer.pid"

# Function to set caffeine state
set_caf() {
    gsettings --schemadir "$SCHEMA_DIR" set "$KEY" cli-toggle "$1"
}

# Check current state
CURRENT_STATE=$(gsettings --schemadir "$SCHEMA_DIR" get "$KEY" cli-toggle)

if [ "$CURRENT_STATE" == "true" ]; then
    # It's currently ON, so turn it OFF
    set_caf false
    
    # Kill the background timer if it exists
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null
        rm "$PID_FILE"
    fi
    echo "Caffeine disabled."
else
    # It's currently OFF, so turn it ON with a timer
    set_caf true
    
    # Start the background timer
    (
        sleep 3600
        set_caf false
        rm "$PID_FILE"
    ) & 
    
    # Save the PID of the background process
    echo $! > "$PID_FILE"
    echo "Caffeine enabled for 1 hour."
fi