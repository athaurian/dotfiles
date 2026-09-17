#!/usr/bin/env sh
set -eu

# Persistent notice before lock. Arg: seconds offset; ID saved for resume dismiss.

id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"
offset="${1:-10}"

dunstify -a idle-warning -u low -t "${offset}000" -p '󰂠 idle warning' "screen locking in ${offset}s" >"$id_file"
