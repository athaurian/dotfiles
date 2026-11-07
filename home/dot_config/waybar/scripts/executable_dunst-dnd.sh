#!/usr/bin/env sh
set -eu

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

APP_NAME="dunst-dnd"
ID_FILE="$(runtime_dir)/dunst_dnd_id"
LOCK_FILE="$(runtime_dir)/dunst_dnd.lock"
DND_PAUSE_LEVEL=50

ICON_ENABLED=""
ICON_DISABLED=""
TEXT_ENABLED="DND enabled"
TEXT_DISABLED="DND disabled"

is_dnd() {
	if command -v dunstctl >/dev/null 2>&1; then
		level=$(timeout 2 dunstctl get-pause-level 2>/dev/null || true)
		[ -n "$level" ] && [ "$level" != "0" ]
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
		send_notice "$APP_NAME" "$ID_FILE" "${ICON_DISABLED} ${TEXT_DISABLED}" "<b>Notifications on.</b> Popups and sounds will appear again."
		timeout 2 dunstctl set-pause-level 0 2>/dev/null || true
	else
		send_notice "$APP_NAME" "$ID_FILE" "${ICON_ENABLED} ${TEXT_ENABLED}" "<b>Notifications silenced.</b> Click the indicator or press Super+Shift+d to disable."
		timeout 2 dunstctl set-pause-level "$DND_PAUSE_LEVEL" 2>/dev/null || true
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
