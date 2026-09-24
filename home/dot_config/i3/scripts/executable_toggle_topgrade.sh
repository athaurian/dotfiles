#!/usr/bin/env sh

set -eu

# Toggle the topgrade terminal (kitty, instance topgrade_term) into and out of
# the scratchpad. Uses shared lib_sway_lock.sh mkdir-based locking.
# The polybar custom/updates module runs this script on click.

app_id=topgrade_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

if i3-msg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'; then
	# Test existence via get_marks (no state change, no render).
	# Show and geometry run as one transaction; i3 renders once. Do not
	# fold the test into the transaction (`if i3-msg "... scratchpad show,
	# resize ..., move ..."`): when hiding, the trailing `move position center`
	# fails on the hidden scratchpad window and poisons the exit status, so
	# every hide falls through and spawns a duplicate terminal.
	i3-msg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

i3-msg exec "kitty --name $app_id -e topgrade"
release_sway_lock "toggle_topgrade"
