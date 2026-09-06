#!/usr/bin/env sh
set -eu

choice_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/sway_restore_choice"

# Skip when there is nothing to bring back: no state file, or one whose
# workspaces, scratchpad, and background apps are all empty.
if ! "$HOME/.config/sway/scripts/session_manager" has-session >/dev/null 2>&1; then
	exit 0
fi

rm -f "$choice_file"

timeout 15 swaynag -t warning \
	-m "restore previous session?" \
	-z "restore" "echo restore > \"$choice_file\"" \
	-z "start fresh" "echo fresh > \"$choice_file\"" &

nag_pid=$!

for i in $(seq 1 18); do
	[ -f "$choice_file" ] && break
	sleep 1
done

if [ -f "$choice_file" ]; then
	choice=$(cat "$choice_file")
	rm -f "$choice_file"
	if [ "$choice" = "restore" ]; then
		kill "$nag_pid" 2>/dev/null || true
		wait "$nag_pid" 2>/dev/null || true
		"$HOME/.config/sway/scripts/session_manager" restore
	fi
else
	kill "$nag_pid" 2>/dev/null || true
	wait "$nag_pid" 2>/dev/null || true
fi
