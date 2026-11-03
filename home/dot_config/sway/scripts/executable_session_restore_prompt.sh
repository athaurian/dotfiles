#!/usr/bin/env sh
set -eu

# Skip when there is nothing to bring back: no state file, or one whose
# workspaces, scratchpad, and background apps are all empty.
session_manager="$HOME/.local/bin/session-manager"
if ! "$session_manager" has-session >/dev/null 2>&1; then
	exit 0
fi

. "$(dirname -- "$0")/lib_confirm.sh"

choice=""
if command -v fuzzel >/dev/null 2>&1; then
	choice="$(confirm_menu --timeout 3 "restore previous session? " "Enter=restore, Esc=start fresh" restore "start fresh")" || choice=""
else
	notify-send -a session-restore -u critical "fuzzel not found" "starting fresh" 2>/dev/null || true
fi

if [ "$choice" = "restore" ]; then
	"$session_manager" restore
fi
