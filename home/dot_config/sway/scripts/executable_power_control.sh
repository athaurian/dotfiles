#!/usr/bin/env sh
set -eu

# Show a keyboard-driven fuzzel menu confirming power/session actions.
# Usage: power_control.sh <poweroff|reboot|suspend|logout>
# Keyboard: type to filter or press Up/Down, Enter confirms the
# highlighted option, Esc cancels.
# Toggle behavior: pressing the same action again dismisses the menu;
# pressing a different action replaces it. State tracked via
# $XDG_RUNTIME_DIR/confirm_action.
#
# Bound to Super+Shift+Backspace/r/z/e in the sway config.

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

. "$(dirname -- "$0")/lib_confirm.sh"

state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/confirm_action"

# Toggle behavior: dismiss a pending power confirm, if any. Power confirms
# are the only fuzzel menus with a "confirm " prompt, so this leaves the
# launcher and the notification-history picker alone.
if command -v pgrep >/dev/null 2>&1 && pgrep -af fuzzel 2>/dev/null | grep -qF "confirm "; then
	current_action=""
	if [ -f "$state_file" ]; then
		current_action=$(cat "$state_file")
	fi
	if command -v pkill >/dev/null 2>&1; then
		pkill -f "fuzzel.*confirm " 2>/dev/null || true
	fi

	# If the same action was triggered again, cancel and exit.
	if [ "$current_action" = "$action" ]; then
		rm -f "$state_file"
		exit 0
	fi
fi

# One-time migration from the swaynag bar: drop its state file and any
# lingering nag left open across the upgrade.
rm -f "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/swaynag_action"
if command -v pkill >/dev/null 2>&1; then
	pkill -x swaynag 2>/dev/null || true
fi

prompt="confirm $action? "

echo "$action" >"$state_file"

choice=""
if command -v fuzzel >/dev/null 2>&1; then
	choice="$(confirm_menu "$prompt" "Enter=yes, Esc=no" yes no)" || choice=""
else
	notify-send -a power-confirm -u critical "fuzzel not found" "power confirmation cancelled" 2>/dev/null || true
fi

# The menu is closed at this point (confirmed or cancelled), so release
# the reservation before running anything.
if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi

if [ "$choice" = "yes" ]; then
	sh -c "$cmd"
fi
