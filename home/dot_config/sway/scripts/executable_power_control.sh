#!/usr/bin/env sh
set -eu

action="${1:-}"

case "$action" in
poweroff) cmd="systemctl poweroff" ;;
reboot) cmd="systemctl reboot" ;;
suspend) cmd="$HOME/.config/sway/scripts/lock.sh --now; systemctl suspend" ;;
logout) cmd="systemctl --user stop sway-session.target; swaymsg exit" ;;
*)
	echo "Usage: $0 <poweroff|reboot|suspend|logout>" >&2
	exit 1
	;;
esac

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
. "$(dirname -- "$0")/lib_confirm.sh"

state_file="$(runtime_dir)/confirm_action"

if command -v pgrep >/dev/null 2>&1 && pgrep -af fuzzel 2>/dev/null | grep -qF "confirm "; then
	current_action=""
	if [ -f "$state_file" ]; then
		current_action=$(cat "$state_file")
	fi
	if command -v pkill >/dev/null 2>&1; then
		pkill -f "fuzzel.*confirm " 2>/dev/null || true
	fi

	if [ "$current_action" = "$action" ]; then
		rm -f "$state_file"
		exit 0
	fi
fi

rm -f "$(runtime_dir)/swaynag_action"
if command -v pkill >/dev/null 2>&1; then
	pkill -x swaynag 2>/dev/null || true
fi

prompt="confirm $action? "

echo "$action" >"$state_file"

choice=""
if command -v fuzzel >/dev/null 2>&1; then
	choice="$(confirm_menu "$prompt" "Enter=yes, Esc=no" yes no)" || choice=""
else
	notify-send -a power-confirm -u critical "Fuzzel not found" "Power confirmation cancelled." 2>/dev/null || true
fi

if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi

if [ "$choice" = "yes" ]; then
	sh -c "$cmd"
fi
