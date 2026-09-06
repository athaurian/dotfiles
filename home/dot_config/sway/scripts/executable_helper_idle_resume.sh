#!/usr/bin/env sh
set -eu

# Dismiss the idle warning notification on user activity.
# Reads the notification ID saved by idle_warning.sh and closes it via dunstctl.
# Called by swayidle resume hook via wrapper_swayidle.sh.

# Dismiss the idle warning notification if it is still showing
id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"

if [ -f "$id_file" ]; then
	nid=$(tr -d '[:space:]' <"$id_file")
	if [ -n "$nid" ]; then
		dunstctl close "$nid" 2>/dev/null || true
	fi
	rm -f "$id_file"
fi
