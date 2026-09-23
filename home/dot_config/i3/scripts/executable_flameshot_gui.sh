#!/usr/bin/env sh
set -eu

# Flameshot region capture. Bound to Shift+Print.
# Restores focus to the window that was active before the editor opened.

WINDOW_ID=$(xdotool getactivewindow)

flameshot gui

xdotool search --sync --class "[Ff]lameshot" >/dev/null 2>&1
while xdotool search --onlyvisible --class "[Ff]lameshot" >/dev/null 2>&1; do
	sleep 0.2
done

xdotool windowactivate "$WINDOW_ID" 2>/dev/null || true
