#!/usr/bin/env sh
set -eu

# Waybar custom/dnd module and toggle.
# DND pauses dunst at DND_PAUSE_LEVEL (partial pause). Script notices for
# direct user feedback (this toggle, caffeine, wallpaper, idle warning,
# clipboard, ...) carry override_pause_level=90 via dunstrc rules and stay
# visible during DND. The screen lock pauses at 100 and hides even those.
# Do not use `set-paused true` here; it sets level 100, which nothing
# bypasses, so the "dnd enabled" notice and all other script notices queue
# silently in history.

APP_NAME="dunst-dnd"
ID_FILE="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_dnd_id"
LOCK_FILE="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_dnd.lock"
# Must stay below the dunstrc dnd_bypass override (90) and below the lock
# pause level (100); keep in sync with lock.sh.
DND_PAUSE_LEVEL=50

ICON_ENABLED=""
ICON_DISABLED=""
TEXT_ENABLED="dnd enabled"
TEXT_DISABLED="dnd disabled"

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
		# Any nonzero pause level counts as DND. The lock screen pauses at
		# 100 and restores the previous level on unlock; a transient 100
		# while locked still reports DND (Waybar is hidden then).
		[ "$(dunstctl get-pause-level 2>/dev/null)" != "0" ] 2>/dev/null
	else
		return 1
	fi
}

toggle_dnd() {
	if ! command -v dunstctl >/dev/null 2>&1; then
		notify-send -u critical "dunst" "dunstctl not found" 2>/dev/null || true
		exit 1
	fi
	# Serialize with flock like the swayidle caffeine toggle.
	exec 9>"$LOCK_FILE"
	flock -w 2 9 || exit 0

	if is_dnd; then
		send_notice "${ICON_DISABLED} ${TEXT_DISABLED}" "<b>notifications on.</b> Popups and sounds will appear again"
		dunstctl set-pause-level 0 2>/dev/null || true
	else
		send_notice "${ICON_ENABLED} ${TEXT_ENABLED}" "<b>notifications silenced.</b> Click the indicator or press Super+Shift+d to disable"
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
