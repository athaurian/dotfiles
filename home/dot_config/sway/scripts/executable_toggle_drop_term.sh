#!/usr/bin/env sh
set -eu

# Toggle the dropdown terminal (foot, app_id=foot_drop) in/out of the scratchpad.
# Uses mkdir-based locking to prevent races from rapid key presses.
# If the marked container exists, shows/hides it; otherwise spawns a new foot
# instance (sway config handles placement via for_window rules).
# Stale locks (>10s or dead PID) are cleaned up automatically.
# Bound to $mod+grave in sway config.

app_id=foot_drop
lockdir="$XDG_RUNTIME_DIR/toggle_drop_term.lock"
lockfile="$lockdir/pid"

have_lock=0
if mkdir "$lockdir" 2>/dev/null; then
	echo $$ >"$lockfile"
	if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
		exit 0
	fi
	have_lock=1
else
	pid=""
	if [ -f "$lockfile" ]; then
		pid=$(tr -d '[:space:]' <"$lockfile")
	fi

	stale=0
	if [ -z "$pid" ]; then
		stale=1
	elif ! echo "$pid" | grep -qE '^[0-9]+$'; then
		stale=1
	elif ! kill -0 "$pid" 2>/dev/null; then
		stale=1
	else
		now=$(date +%s)
		mtime=$(date -r "$lockdir" +%s 2>/dev/null || echo 0)
		if [ $((now - mtime)) -gt 10 ]; then
			stale=1
		fi
	fi

	if [ "$stale" -eq 1 ]; then
		rm -rf "$lockdir"
		if mkdir "$lockdir" 2>/dev/null; then
			echo $$ >"$lockfile"
			if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
				exit 0
			fi
			have_lock=1
		fi
	fi
fi

if [ "$have_lock" -ne 1 ]; then
	exit 0
fi

if swaymsg "[con_mark=drop_term] scratchpad show" >/dev/null 2>&1; then
	rm -rf "$lockdir"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id"
rm -rf "$lockdir"
