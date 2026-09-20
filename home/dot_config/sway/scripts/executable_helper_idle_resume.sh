#!/usr/bin/env sh
set -eu

# Dismisses helper_idle_warning.sh's notice (swayidle resume hook).

id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"

if [ -f "$id_file" ]; then
	nid=$(tr -d '[:space:]' <"$id_file")
	if [ -n "$nid" ]; then
		dunstctl close "$nid" 2>/dev/null || true
	fi
	rm -f "$id_file"
fi
