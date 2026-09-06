#!/usr/bin/env sh
set -eu

# Toggle the dropdown terminal into and out of the scratchpad. It uses foot
# with app_id foot_drop.
# Uses the shared lib_sway_lock.sh mkdir-based locking to prevent races
# from rapid key presses.
# If the marked container exists, show or hide it. Otherwise spawn a new
# foot instance (sway config handles placement via for_window rules).
# Stale locks (>10s or dead PID) are cleaned up automatically.
# Bound to $mod+grave in sway config.

app_id=foot_drop

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_drop_term" || exit 0

if swaymsg "[con_mark=drop_term] scratchpad show" >/dev/null 2>&1; then
	release_sway_lock "toggle_drop_term"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id"

# Wait for the foot window to appear while still holding the lock, so a
# second keypress sees the mark instead of spawning its own terminal.
i=0
while [ "$i" -lt 40 ]; do
	if swaymsg -t get_marks 2>/dev/null | grep -qF '"drop_term"'; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
release_sway_lock "toggle_drop_term"
