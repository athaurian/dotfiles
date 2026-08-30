#!/usr/bin/env sh

set -eu

# Toggle the topgrade terminal (foot, app_id=foot_topgrade) in/out of the scratchpad.
# Mirrors toggle_drop_term.sh with mkdir-based locking.
# Bound via Waybar custom/updates on-click.

app_id=foot_topgrade
lockdir="$XDG_RUNTIME_DIR/toggle_topgrade.lock"
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

if swaymsg "[con_mark=topgrade_term] scratchpad show" >/dev/null 2>&1; then
	# Sway's `move position center` only works on the visible workspace,
	# so centering must happen after `scratchpad show` (the for_window
	# rule can only size and hide the window while it is still on the
	# scratchpad). Re-apply geometry here so resize + center actually
	# take effect. The `|| true` keeps `set -e` from aborting if the
	# mark disappeared between the two swaymsg calls (for example, window closed).
	swaymsg "[con_mark=topgrade_term] resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	rm -rf "$lockdir"
	exit 0
fi

swaymsg exec "foot --app-id=$app_id -e sh -c 'topgrade; pkill -RTMIN+8 waybar 2>/dev/null || true'"
rm -rf "$lockdir"
