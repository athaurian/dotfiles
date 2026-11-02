#!/usr/bin/env sh
set -eu

# Ask whether to restore the previous session via a keyboard-driven
# fuzzel menu. Type to filter or press Up/Down, Enter restores, Esc or
# the 15 second timeout starts fresh (the safe default). Runs in the
# background from autostart.sh so login never blocks.

# Skip when there is nothing to bring back: no state file, or one whose
# workspaces, scratchpad, and background apps are all empty.
if ! "$HOME/.config/sway/scripts/session_manager" has-session >/dev/null 2>&1; then
	exit 0
fi

. "$(dirname -- "$0")/lib_confirm.sh"

choice=""
if command -v fuzzel >/dev/null 2>&1; then
	choice="$(confirm_menu --timeout 15 "restore previous session? " "Enter=restore, Esc=start fresh" restore "start fresh")" || choice=""
else
	notify-send -a session-restore -u critical "fuzzel not found" "starting fresh" 2>/dev/null || true
fi

if [ "$choice" = "restore" ]; then
	"$HOME/.config/sway/scripts/session_manager" restore
fi
