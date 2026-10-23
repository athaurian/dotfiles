#!/usr/bin/env sh

set -eu

# Toggle the fzf clipboard history picker. A second press hides the
# visible picker, and the lock ignores repeats while it spawns.

mark=clipboard_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_clipboard" || exit 0

# The picker itself is shared, so this script is sway's lifecycle around it.
picker="$HOME/.local/bin/clipboard"

# The mark probe must not toggle visibility or steal focus.
has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

show_picker() {
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
}

if has_mark; then
	show_picker
	release_sway_lock "toggle_clipboard"
	exit 0
fi

if [ ! -x "$picker" ]; then
	release_sway_lock "toggle_clipboard"
	exit 0
fi

"$picker" &

# Hold the lock until the mark appears, so a second keypress is ignored
# while the first spawn starts. The timeout covers exits that open no
# window (empty history, missing dependencies).
i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
if has_mark; then
	# Pickers start hidden, so map the new one already centered.
	show_picker
fi
release_sway_lock "toggle_clipboard"
