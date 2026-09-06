#!/usr/bin/env sh
set -eu

# Toggle swayidle on/off ("caffeine mode").
# Bound to $mod+Shift+i with --no-repeat in sway config.

unit="swayidle-unlocked.service"
id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/caffeine_toggle_id"
lock_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/caffeine_toggle.lock"
app_name="caffeine-toggle"

# Serialize toggle invocations.
# This waits briefly instead of silently dropping a rapid second invocation.
exec 9>"$lock_file"
flock -w 2 9 || exit 0

send_notice() {
	summary=$1
	body=$2

	old_id=0
	if [ -s "$id_file" ]; then
		old_id=$(tr -cd '0-9' <"$id_file")
		[ -n "$old_id" ] || old_id=0
	fi

	new_id=""

	if [ "$old_id" -gt 0 ] 2>/dev/null; then
		new_id=$(
			dunstify \
				-a "$app_name" \
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
				-a "$app_name" \
				-u low \
				-t 3000 \
				-p \
				"$summary" \
				"$body"
		)
		new_id=$(printf '%s' "$new_id" | tr -cd '0-9')
	fi

	tmp="${id_file}.$$"
	printf '%s\n' "$new_id" >"$tmp"
	mv -f "$tmp" "$id_file"
}

unit_state() {
	systemctl --user show "$unit" -p ActiveState --value 2>/dev/null || printf '%s\n' unknown
}

start_unit() {
	systemctl --user reset-failed "$unit" 2>/dev/null || true

	if ! systemctl --user start "$unit"; then
		state=$(unit_state)
		send_notice " caffeine toggle failed" "systemctl start failed; $unit state: $state"
		exit 1
	fi

	state=$(unit_state)

	if [ "$state" = "active" ]; then
		send_notice "󰒲 caffeine mode off" "<b>swayidle restarted.</b> normal idle rules apply"
	else
		send_notice " caffeine toggle failed" "after start, $unit state is: $state"
		exit 1
	fi
}

stop_unit() {
	if ! systemctl --user stop "$unit"; then
		state=$(unit_state)
		send_notice " caffeine toggle failed" "systemctl stop failed; $unit state: $state"
		exit 1
	fi

	state=$(unit_state)

	if [ "$state" = "inactive" ]; then
		send_notice "󰒳 caffeine mode on" "<b>swayidle stopped.</b> we're staying up indefinitely"
	else
		send_notice " caffeine toggle failed" "after stop, $unit state is: $state"
		exit 1
	fi
}

state=$(unit_state)

case "$state" in
active | activating | reloading)
	stop_unit
	;;

inactive | failed)
	start_unit
	;;

deactivating)
	# A stop is already in progress. Finish that transition, then toggle back on.
	if ! systemctl --user stop "$unit"; then
		state=$(unit_state)
		send_notice " caffeine toggle failed" "could not finish pending stop; $unit state: $state"
		exit 1
	fi

	start_unit
	;;

*)
	send_notice " caffeine toggle failed" "$unit is in unexpected state: $state"
	exit 1
	;;
esac
