#!/usr/bin/env sh
set -eu

# Flameshot capture of the focused window's geometry. Bound to Ctrl+Print.
# -c also copies the capture, matching the sway path's clipboard copy.

WINDOW_ID=$(xdotool getactivewindow)

save_dir="$HOME/Pictures/Screenshots"
mkdir -p "$save_dir"

unset X Y WIDTH HEIGHT
eval "$(xdotool getwindowgeometry --shell "$WINDOW_ID")"

flameshot gui -p "$save_dir" -c --region "${WIDTH}x${HEIGHT}+${X}+${Y}"
