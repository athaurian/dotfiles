#!/usr/bin/env sh

set -eu

# Show the fzf clipboard history picker. It uses foot with app_id
# foot_clipboard and allows only one instance. If a picker window is
# already open, toggle its scratchpad visibility instead of spawning
# another one. Uses the shared lib_sway_lock.sh mkdir-based locking. Unlike
# the dropdown and topgrade terminals, the picker is one-shot. It exits
# after a selection, so hiding it just parks it until the next press. The
# lock is held until the new window's mark appears, so rapid keybind
# repeats queue behind the first spawn instead of opening extra terminals.

mark=clipboard_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_clipboard" || exit 0

# Probe for the mark without changing state for the wait loop in the
# following section. `scratchpad show` would toggle visibility, and
# `focus` would steal focus on every poll.
has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	# has_mark tests existence without changing state (no render).
	# Show + geometry then runs as one transaction so Sway renders
	# once. NOTE: do NOT fold the test into the transaction
	# (`if swaymsg "... scratchpad show, resize ..., move ..."`): when
	# hiding, the trailing `move position center` fails on the hidden
	# scratchpad window and poisons the exit status, so every hide
	# would fall through and spawn a duplicate picker.
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_clipboard"
	exit 0
fi

"$HOME/.config/sway/scripts/clipboard" &

# Wait for the foot window to appear while still holding the lock, so a
# second keypress sees the mark instead of spawning its own terminal.
# The empty-history and missing-dependency paths exit without opening a
# window, hence the timeout.
i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
if has_mark; then
	# New picker starts hidden (no auto-show in its for_window rule),
	# so show + geometry in one transaction maps it already centered.
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
fi
release_sway_lock "toggle_clipboard"
