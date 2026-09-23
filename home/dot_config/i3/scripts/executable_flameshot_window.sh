#!/usr/bin/env sh
set -eu

# Flameshot capture of the focused window's geometry. Bound to Ctrl+Print.
# Restores focus to the window that was active before the editor opened.

WINDOW_ID=$(xdotool getactivewindow)

unset X Y WIDTH HEIGHT
eval "$(xdotool getwindowgeometry --shell "$WINDOW_ID")"

flameshot gui --region "${WIDTH}x${HEIGHT}+${X},${Y}"

xdotool search --sync --class "[Ff]lameshot" >/dev/null 2>&1
while xdotool search --onlyvisible --class "[Ff]lameshot" >/dev/null 2>&1; do
	sleep 0.2
done

xdotool windowactivate "$WINDOW_ID" 2>/dev/null || true
