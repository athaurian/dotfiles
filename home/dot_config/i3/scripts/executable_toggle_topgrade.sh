#!/usr/bin/env sh
set -eu

app_id=topgrade_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_topgrade" || exit 0

has_mark() {
	i3-msg -t get_marks 2>/dev/null | grep -qF '"topgrade_term"'
}

if has_mark; then
	# Keep the mark test separate from the combined command. Otherwise hiding
	# a visible terminal fails the command and the script spawns a duplicate.
	i3-msg "[con_mark=topgrade_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_topgrade"
	exit 0
fi

i3-msg "exec --no-startup-id kitty --name $app_id -e $HOME/.config/i3/scripts/wrapper_topgrade.sh"

# Keep the lock until the mark shows. A second keypress does nothing while
# the first window starts.
i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
release_sway_lock "toggle_topgrade"
