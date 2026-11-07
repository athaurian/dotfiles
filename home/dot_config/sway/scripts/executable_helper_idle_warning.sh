#!/usr/bin/env sh
set -eu

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

id_file="$(runtime_dir)/idle_warning_id"
offset="${1:-10}"

dunstify -a idle-warning -u low -t "${offset}000" -p '󰂠 Idle warning' "Screen locking in ${offset}s." >"$id_file"
