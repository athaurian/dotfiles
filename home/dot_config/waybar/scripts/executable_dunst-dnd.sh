#!/usr/bin/env sh
set -eu

APP_NAME="dunst-dnd"
ID_FILE="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_dnd_id"
LOCK_FILE="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_dnd.lock"
DND_PAUSE_LEVEL=50

ICON_ENABLED=""
ICON_DISABLED=""
TEXT_ENABLED="DND enabled"
TEXT_DISABLED="DND disabled"

send_notice() {
	summary=$1
	body=$2

	old_id=0
	if [ -s "$ID_FILE" ]; then
		old_id=$(tr -cd '0-9' <"$ID_FILE")
		[ -n "$old_id" ] || old_id=0
	fi

	new_id=""

	if [ "$old_id" -gt 0 ] 2>/dev/null; then
		new_id=$(
			dunstify \
				-a "$APP_NAME" \
				-u low \
				-t 3000 \
				-p \
				-r "$old_id" \
				"$summary" \
				"$body" 2>/dev/null || true
		)
		new_id=$(printf '%s' "$new_id" | tr -cd '0-9')
	fi

	if [ -z "$new_id" ]; then
		new_id=$(
			dunstify \
				-a "$APP_NAME" \
				-u low \
				-t 3000 \
				-p \
				"$summary" \
				"$body"
		)
		new_id=$(printf '%s' "$new_id" | tr -cd '0-9')
	fi

	tmp="${ID_FILE}.$$"
	printf '%s\n' "$new_id" >"$tmp"
	mv -f "$tmp" "$ID_FILE"
}

is_dnd() {
	if command -v dunstctl >/dev/null 2>&1; then
		[ "$(dunstctl get-pause-level 2>/dev/null)" != "0" ] 2>/dev/null
	else
		return 1
	fi
}

toggle_dnd() {
	if ! command -v dunstctl >/dev/null 2>&1; then
		notify-send -u critical "Dunst" "Dunstctl not found." 2>/dev/null || true
		exit 1
	fi
	exec 9>"$LOCK_FILE"
	flock -w 2 9 || exit 0

	if is_dnd; then
		send_notice "${ICON_DISABLED} ${TEXT_DISABLED}" "<b>Notifications on.</b> Popups and sounds will appear again."
		dunstctl set-pause-level 0 2>/dev/null || true
	else
		send_notice "${ICON_ENABLED} ${TEXT_ENABLED}" "<b>Notifications silenced.</b> Click the indicator or press Super+Shift+d to disable."
		dunstctl set-pause-level "$DND_PAUSE_LEVEL" 2>/dev/null || true
	fi
	pkill -RTMIN+9 waybar 2>/dev/null || true
}

if [ "${1:-}" = "--toggle" ]; then
	toggle_dnd
fi

if is_dnd; then
	printf '{"text":"%s","tooltip":"Click to disable (Super+Shift+d)","class":"enabled","alt":"enabled"}\n' "$ICON_ENABLED"
else
	printf '{"text":"%s","tooltip":"Click to enable (Super+Shift+d)","class":"ok","alt":"ok"}\n' "$ICON_DISABLED"
fi
