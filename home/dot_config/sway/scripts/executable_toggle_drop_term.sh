#!/usr/bin/env sh
set -eu

# Sway compares the title as a substring. The window class and the mark use
# the same name.
mark=drop_term

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
acquire_lock "toggle_drop_term" || exit 0

has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_lock "toggle_drop_term"
	exit 0
fi

swaymsg exec "kitty --class=$mark --title=$mark"

i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
release_lock "toggle_drop_term"
