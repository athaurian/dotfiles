#!/usr/bin/env sh
set -eu

# The picker tool starts kitty with a title only. The rule anchors the title
# to an exact match.
mark=clipboard_term

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
acquire_lock "toggle_clipboard" || exit 0

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
	release_lock "toggle_clipboard"
	exit 0
fi

if [ ! -x "$picker" ]; then
	release_lock "toggle_clipboard"
	exit 0
fi

"$picker" &

# Keep the lock until the mark shows. A second keypress does nothing while
# the first window starts. The timeout covers exits that open no window,
# for example an empty history or a missing dependency.
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
release_lock "toggle_clipboard"
