#!/usr/bin/env sh
set -eu

# Rofi-confirmed power and session actions.
# Usage: power_control.sh <poweroff|reboot|suspend|logout>
# Same action re-invoked dismisses; different action replaces (state in $XDG_RUNTIME_DIR/confirm_action).

action="${1:-}"

case "$action" in
poweroff) cmd="systemctl poweroff" ;;
reboot) cmd="systemctl reboot" ;;
# lock.sh --now blocks until the screen unlocks; suspend instead waits
# on the sleep-lock fd that xss-lock hands to its own lock.sh instance.
suspend) cmd="$HOME/.config/i3/scripts/lock.sh --now & systemctl suspend" ;;
logout) cmd="systemctl --user stop i3-session.target; i3-msg exit" ;;
*)
	echo "Usage: $0 <poweroff|reboot|suspend|logout>" >&2
	exit 1
	;;
esac

# confirm_menu PROMPT PLACEHOLDER OPTION...: prints the choice; returns 1
# on cancel, timeout, or missing rofi.
confirm_menu() {
	confirm_prompt="${1:-}"
	confirm_placeholder="${2:-}"
	shift 2 || return 1
	if [ "$#" -eq 0 ] || [ -z "$confirm_prompt" ]; then
		return 1
	fi
	if ! command -v rofi >/dev/null 2>&1; then
		return 1
	fi
	# The theme never renders the -mesg widget, so the hint rides in the
	# entry placeholder instead (fuzzel passes it as --placeholder).
	confirm_choice="$(printf '%s\n' "$@" | rofi -dmenu -p "$confirm_prompt" -theme-str "entry { placeholder: \"$confirm_placeholder\"; }")" || return 1
	if [ -z "$confirm_choice" ]; then
		return 1
	fi
	printf '%s\n' "$confirm_choice"
}

state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/confirm_action"

# Only power confirmations use a "confirm " prompt; launcher and history pickers never match.
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
	notify-send -a power-confirm -u critical "rofi not found" "power confirmation cancelled" 2>/dev/null || true
fi

if [ -f "$state_file" ] && [ "$(cat "$state_file")" = "$action" ]; then
	rm -f "$state_file"
fi

if [ "$choice" = "yes" ]; then
	sh -c "$cmd"
fi
