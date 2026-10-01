#!/usr/bin/env sh
set -eu

id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"
offset="${1:-10}"

dunstify -a idle-warning -u low -t "${offset}000" -p '󰂠 Idle warning' "Screen locking in ${offset}s." >"$id_file"
