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

confirm_menu() {
	confirm_prompt="${1:-}"
	confirm_placeholder="${2:-}"
	shift 2 || return 1
	if [ "$#" -eq 0 ] || [ -z "$confirm_prompt" ]; then
		return 1
	fi
	if ! command -v fuzzel >/dev/null 2>&1; then
		return 1
	fi
	confirm_choice="$(printf '%s\n' "$@" | fuzzel --dmenu --anchor=center --prompt "$confirm_prompt" --placeholder "$confirm_placeholder" --lines "$#")" || return 1
	if [ -z "$confirm_choice" ]; then
		return 1
	fi
	printf '%s\n' "$confirm_choice"
}

state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/confirm_action"

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
	notify-send -a power-confirm -u critical "Fuzzel not found" "Power confirmation cancelled." 2>/dev/null || true
fi

if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi

if [ "$choice" = "yes" ]; then
	sh -c "$cmd"
fi
