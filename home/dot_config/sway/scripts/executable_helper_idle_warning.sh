#!/usr/bin/env sh
set -eu

# Shows a persistent notice before locking. The argument is the seconds
# offset. The resume hook uses the saved ID to dismiss it.

id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"
offset="${1:-10}"

dunstify -a idle-warning -u low -t "${offset}000" -p '󰂠 idle warning' "screen locking in ${offset}s" >"$id_file"
