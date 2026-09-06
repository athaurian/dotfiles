#!/usr/bin/env sh
set -eu

# Send a persistent low-urgency notification before screen lock.
# Uses dunstify -p to capture the notification ID, stored in
# $XDG_RUNTIME_DIR/idle_warning_id for dismissal by idle_resume.sh.
# Called by swayidle timeout via wrapper_swayidle.sh. Arg: seconds offset.

# Send a persistent idle warning notification and store its ID
id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/idle_warning_id"
offset="${1:-10}"

dunstify -a idle-warning -u low -t "${offset}000" -p '󰂠 idle warning' "screen locking in ${offset}s" >"$id_file"
