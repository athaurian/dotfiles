#!/usr/bin/env sh

set -eu

# Clicking the custom/updates module in Polybar runs this script.

app_id=topgrade_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if i3-msg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# The show, resize, and move below run as one i3-msg command for a
	# single i3 render. The existence test must stay out of that command.
	# If the script tested with that command, `scratchpad show` would hide
	# a visible terminal, the trailing `move position center` would fail on
	# the now-hidden window, and i3-msg would report failure. The script
	# would read that failure as a missing terminal and spawn a duplicate.
	i3-msg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

i3-msg "exec --no-startup-id kitty --name $app_id -e $HOME/.config/i3/scripts/wrapper_topgrade.sh"
release_sway_lock "toggle_topgrade"
