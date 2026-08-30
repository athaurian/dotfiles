#!/usr/bin/env sh
set -eu

# Waybar custom/dnd module + toggle.
# Shows DND state from mako and toggles `do-not-disturb` mode on click.

MODE="do-not-disturb"
APP_NAME="mako-dnd"
ID_FILE="$XDG_RUNTIME_DIR/mako_dnd_id"
LOCK_FILE="$XDG_RUNTIME_DIR/mako_dnd.lock"

# Icons and text labels
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
			notify-send \
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
			notify-send \
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
	if command -v makoctl >/dev/null 2>&1; then
		# makoctl mode prints current modes, one per line.
		makoctl mode 2>/dev/null | grep -qx "$MODE" 2>/dev/null
	else
		return 1
	fi
}

toggle_dnd() {
	if ! command -v makoctl >/dev/null 2>&1; then
		notify-send -u critical "mako" "makoctl not found" 2>/dev/null || true
		exit 1
	fi
	# Serialize like toggle_idle.sh. Flock briefly
	exec 9>"$LOCK_FILE"
	flock -w 2 9 || exit 0

	if is_dnd; then
		send_notice "${ICON_DISABLED} ${TEXT_DISABLED}" "<b>notifications on.</b> popups and sounds will appear again"
		makoctl mode -r "$MODE" 2>/dev/null || true
	else
		send_notice "${ICON_ENABLED} ${TEXT_ENABLED}" "<b>notifications silenced.</b> click the indicator or press Super+Shift+d to disable"
		makoctl mode -a "$MODE" 2>/dev/null || true
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
