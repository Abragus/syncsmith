#!/bin/bash

PIPE="/tmp/brightness_pipe"
DEVICE="amdgpu_bl1"

if [ -e "$PIPE" ] && [ ! -p "$PIPE" ]; then
    rm -f "$PIPE"
fi
[ -p "$PIPE" ] || mkfifo "$PIPE"

MAX=$(brightnessctl -d "$DEVICE" max 2>/dev/null || echo 65535)
STEP=$(( MAX * 10 / 100 )) # 10% steps

show_osd() {
    local target_val=$1
    local level=$(awk "BEGIN {print $target_val / $MAX}")
    
    # Run gdbus in the background (&) so it never slows down the script
    gdbus call --session \
        --dest org.gnome.Shell \
        --object-path /org/gnome/Shell/Extensions/SmoothBrightness \
        --method org.gnome.Shell.Extensions.SmoothBrightness.ShowOSD \
        $level >/dev/null 2>&1 &
}

animate() {
    local start=$1
    local end=$2
    local dist=$(( end - start ))
    local steps=25
    
    if [ "$dist" -eq 0 ]; then
        return
    fi
    
    for ((i=1; i<=steps; i++)); do
        local current=$(( start + (dist * i / steps) ))
        brightnessctl -q -d "$DEVICE" set "$current"
        sleep 0.005
    done
    
    # Ensure it lands exactly on the target value at the end
    brightnessctl -q -d "$DEVICE" set "$end"
}

target=$(brightnessctl -d "$DEVICE" get)
anim_pid=""

exec 3<> "$PIPE"

while read -r cmd <&3; do
    if [[ "$cmd" != "up" && "$cmd" != "down" ]]; then
        continue
    fi

    # Kill running animation instantly with -9 so direction changes are immediate
    if [[ -n "$anim_pid" ]] && kill -0 "$anim_pid" 2>/dev/null; then
        kill -9 "$anim_pid" 2>/dev/null
        wait "$anim_pid" 2>/dev/null
    else
        target=$(brightnessctl -d "$DEVICE" get)
    fi

    if [[ "$cmd" == "up" ]]; then
        target=$(( target + STEP ))
    elif [[ "$cmd" == "down" ]]; then
        target=$(( target - STEP ))
    fi

    (( target > MAX )) && target=$MAX
    (( target < 0 )) && target=0

    # Call OSD exactly once with the target value before the animation starts
    show_osd "$target"

    current=$(brightnessctl -d "$DEVICE" get)
    animate "$current" "$target" &
    anim_pid=$!
done