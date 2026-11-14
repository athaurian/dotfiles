#!/usr/bin/env sh
set -eu

# The sway rule anchors the spawn title. The window keeps the kitty app id,
# so the status bar shows the kitty icon.
mark=drop_term

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
exec 9>"$(runtime_dir)/toggle_drop_term.flock"
flock -n 9 || exit 0

has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	exec 9>&-
	exit 0
fi

swaymsg exec "kitty --title=$mark"

i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
exec 9>&-
