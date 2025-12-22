#!/bin/bash

USER_NAME="gustav"
INTERFACE=$1
STATUS=$2
TARGET_SSIDS=("eduroam" ".Oresundstag_Wi-Fi")

# Your specific built-in speaker sink
SPEAKER_SINK="alsa_output.pci-0000_c1_00.6.analog-stereo"

if [ "$STATUS" = "up" ]; then
    
    # 1. Only run for Wi-Fi interfaces
    INT_TYPE=$(nmcli -t -f GENERAL.TYPE dev show "$INTERFACE" | cut -d':' -f2)
    if [ "$INT_TYPE" != "wifi" ]; then
        exit 0
    fi

    # 2. Get the current SSID
    CURRENT_SSID=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | tail -n1 | cut -d':' -f2)

    for TARGET_SSID in "${TARGET_SSIDS[@]}"; do
        if [ "$CURRENT_SSID" == "$TARGET_SSID" ]; then
            
            # 3. Check if the speaker sink exists/is active
            # This prevents errors if the hardware is temporarily busy
            SINK_EXISTS=$(sudo -u $USER_NAME pactl list short sinks | grep "$SPEAKER_SINK")

            if [ -n "$SINK_EXISTS" ]; then
                # Get current volume of the SPECIFIC sink
                CURRENT_VOLUME=$(sudo -u $USER_NAME pactl get-sink-volume "$SPEAKER_SINK" | awk '/^Volume:/ {print $5}' | sed 's/%//')

                if [ -n "$CURRENT_VOLUME" ] && [ "$CURRENT_VOLUME" -ne 0 ]; then
                    # Mute only the built-in speakers
                    sudo -u $USER_NAME pactl set-sink-volume "$SPEAKER_SINK" 0%
                    
                    # Send notification
                    sudo -u $USER_NAME notify-send -a "Wi-Fi Volume Controller" "Speakers Muted" "Connected to $CURRENT_SSID. Built-in speakers set to 0%."
                fi
            fi
            break
        fi
    done
fi