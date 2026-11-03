#!/usr/bin/env sh
set -eu

action="${1:-}"

session_manager="$HOME/.local/bin/session-manager"

case "$action" in
poweroff) cmd="$session_manager save --quiet; systemctl poweroff" ;;
reboot) cmd="$session_manager save --quiet; systemctl reboot" ;;
suspend) cmd="systemctl suspend" ;;
logout) cmd="$session_manager save --quiet; systemctl --user stop i3-session.target; i3-msg exit" ;;
*)
	echo "Usage: $0 <poweroff|reboot|suspend|logout>" >&2
	exit 1
	;;
esac

. "$(dirname -- "$0")/lib_confirm.sh"

state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/confirm_action"

if command -v pgrep >/dev/null 2>&1 && pgrep -af rofi 2>/dev/null | grep -qF "confirm "; then
	current_action=""
	if [ -f "$state_file" ]; then
		current_action=$(cat "$state_file")
	fi
	if command -v pkill >/dev/null 2>&1; then
		pkill -f "rofi.*confirm " 2>/dev/null || true
	fi

	if [ "$current_action" = "$action" ]; then
		rm -f "$state_file"
		exit 0
	fi
fi

prompt="confirm $action? "

echo "$action" >"$state_file"

choice=""
if command -v rofi >/dev/null 2>&1; then
	choice="$(confirm_menu "$prompt" "Enter=yes, Esc=no" yes no)" || choice=""
else
	notify-send -a power-confirm -u critical "Rofi not found" "Power confirmation cancelled." 2>/dev/null || true
fi

if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi

if [ "$choice" = "yes" ]; then
	sh -c "$cmd"
fi
