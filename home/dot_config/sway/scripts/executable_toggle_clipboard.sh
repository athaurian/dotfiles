#!/usr/bin/env sh

set -eu

# Toggle the fzf clipboard history picker. Only one instance runs: a
# second press hides the visible picker instead of spawning another.
# The picker exits after each selection. Uses the shared
# lib_sway_lock.sh locking, held until the new window's mark appears
# so rapid keybind repeats queue behind the first spawn.

mark=clipboard_term

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_clipboard" || exit 0

# State-free mark probe for the toggle below and the wait loop:
# `scratchpad show` would toggle visibility, `focus` would steal
# focus on every poll.
has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	# Test first, then show. Folding the test into the swaymsg call
	# breaks hiding: `move position center` fails on a hidden
	# scratchpad window, and the failed status would spawn a
	# duplicate picker. The combined show call renders once.
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_clipboard"
	exit 0
fi

"$HOME/.config/sway/scripts/clipboard" &

# Hold the lock until the mark appears, so a second keypress queues
# behind the first spawn. The timeout covers exits that open no
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
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
fi
release_sway_lock "toggle_clipboard"
