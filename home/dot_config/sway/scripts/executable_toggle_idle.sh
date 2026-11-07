#!/usr/bin/env sh
set -eu

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

unit="swayidle-unlocked.service"
id_file="$(runtime_dir)/caffeine_toggle_id"
lock_file="$(runtime_dir)/caffeine_toggle.lock"
app_name="caffeine-toggle"

exec 9>"$lock_file"
flock -w 2 9 || exit 0

unit_state() {
	systemctl --user show "$unit" -p ActiveState --value 2>/dev/null || printf '%s\n' unknown
}

start_unit() {
	systemctl --user reset-failed "$unit" 2>/dev/null || true

	if ! systemctl --user start "$unit"; then
		state=$(unit_state)
		send_notice "$app_name" "$id_file" " Caffeine toggle failed" "Systemctl start failed; $unit state: $state."
		exit 1
	fi

	state=$(unit_state)

	if [ "$state" = "active" ]; then
		send_notice "$app_name" "$id_file" "󰒲 Caffeine mode off" "<b>swayidle restarted.</b> Normal idle rules apply."
	else
		send_notice "$app_name" "$id_file" " Caffeine toggle failed" "After start, $unit state is: $state."
		exit 1
	fi
}

stop_unit() {
	if ! systemctl --user stop "$unit"; then
		state=$(unit_state)
		send_notice "$app_name" "$id_file" " Caffeine toggle failed" "Systemctl stop failed; $unit state: $state."
		exit 1
	fi

	state=$(unit_state)

	if [ "$state" = "inactive" ]; then
		send_notice "$app_name" "$id_file" "󰒳 Caffeine mode on" "<b>swayidle stopped.</b> The system stays awake indefinitely."
	else
		send_notice "$app_name" "$id_file" " Caffeine toggle failed" "After stop, $unit state is: $state."
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
	if ! systemctl --user stop "$unit"; then
		state=$(unit_state)
		send_notice "$app_name" "$id_file" " Caffeine toggle failed" "Could not finish pending stop; $unit state: $state."
		exit 1
	fi

	start_unit
	;;

*)
	send_notice "$app_name" "$id_file" " Caffeine toggle failed" "Unit $unit is in unexpected state: $state."
	exit 1
	;;
esac
