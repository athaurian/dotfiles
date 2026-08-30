#!/usr/bin/env sh
set -eu

# Show a swaynag confirmation dialog for power/session-lifecycle actions.
# Usage: power_control.sh <poweroff|reboot|suspend|logout>
# Toggle behavior: pressing the same action again dismisses the dialog;
# pressing a different action replaces it. State tracked via
# $XDG_RUNTIME_DIR/swaynag_action.

action="${1:-}"

case "$action" in
poweroff) cmd="$HOME/.config/sway/scripts/session_manager save --quiet; systemctl poweroff" ;;
reboot) cmd="$HOME/.config/sway/scripts/session_manager save --quiet; systemctl reboot" ;;
suspend) cmd="systemctl suspend" ;;
logout) cmd="$HOME/.config/sway/scripts/session_manager save --quiet; systemctl --user stop sway-session.target; swaymsg exit" ;;
*)
	echo "Usage: $0 <poweroff|reboot|suspend|logout>" >&2
	exit 1
	;;
esac

state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/swaynag_action"

# Toggle behavior: if swaynag is running, kill it.
if pgrep -x swaynag >/dev/null 2>&1; then
	current_action=""
	if [ -f "$state_file" ]; then
		current_action=$(cat "$state_file")
	fi
	pkill -x swaynag

	# If the same action was triggered again, cancel and exit.
	if [ "$current_action" = "$action" ]; then
		rm -f "$state_file"
		exit 0
	fi
fi

msg="confirm $action?"
confirm_msg="yes"
cancel_msg="no"

echo "$action" >"$state_file"

swaynag -t warning \
	-m "$msg" \
	-B "$confirm_msg" "$cmd" \
	-s x \
	-Z "$cancel_msg" true

# Cleanup state file if this instance's action is still the one pending
if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi
