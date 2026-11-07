#!/usr/bin/env sh
set -eu

# The sway rule matches this class. Keep the flag.
mark=topgrade_term

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
acquire_lock "toggle_topgrade" || exit 0

has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	# Keep the mark test separate from the combined command. Otherwise hiding
	# a visible terminal fails the command and the script spawns a duplicate.
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_lock "toggle_topgrade"
	exit 0
fi

swaymsg exec "kitty --class=$mark --title=$mark -e sh -c 'if topgrade; then pkill -RTMIN+8 waybar 2>/dev/null || true; else printf \"topgrade failed; press Enter to close\n\"; read -r _ || true; fi'"

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
release_lock "toggle_topgrade"
