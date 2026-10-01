#!/usr/bin/env sh
set -eu

WINDOW_ID=$(xdotool getactivewindow)

save_dir="$HOME/Pictures/Screenshots"
mkdir -p "$save_dir"

unset X Y WIDTH HEIGHT
eval "$(xdotool getwindowgeometry --shell "$WINDOW_ID")"

flameshot gui -p "$save_dir" -c --region "${WIDTH}x${HEIGHT}+${X}+${Y}"
