#!/usr/bin/env sh
set -eu

# Toggle caffeine mode: the X screensaver and DPMS timers off and on.
# Native X11 idle has no daemon to pause, so the timers themselves are the state.

id_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/caffeine_toggle_id"
lock_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/caffeine_toggle.lock"
app_name="caffeine-toggle"

# Serialize rapid toggles.
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

screensaver_timeout() {
	# xset q prints "timeout:  N"; 0 means the screensaver is off.
	xset q 2>/dev/null | sed -n 's/.*timeout: *\([0-9]\+\).*/\1/p' | head -n 1
}

disable_timers() {
	if ! xset s off; then
		send_notice " caffeine toggle failed" "<b>xset s off failed.</b>"
		exit 1
	fi
	if ! xset -dpms; then
		send_notice " caffeine toggle failed" "<b>xset -dpms failed.</b>"
		exit 1
	fi
	send_notice "󰒳 caffeine mode on" "<b>idle timers disabled.</b> The system stays awake indefinitely"
}

enable_timers() {
	if ! xset s 30; then
		send_notice " caffeine toggle failed" "<b>xset s 30 failed.</b>"
		exit 1
	fi
	if ! xset +dpms || ! xset dpms 90 90 90; then
		send_notice " caffeine toggle failed" "<b>xset dpms failed.</b>"
		exit 1
	fi
	send_notice "󰒲 caffeine mode off" "<b>idle timers restored.</b> Normal idle rules apply"
}

timeout_value=$(screensaver_timeout)

case "$timeout_value" in
0) enable_timers ;;
"")
	send_notice " caffeine toggle failed" "<b>could not read the screensaver timeout.</b>"
	exit 1
	;;
*) disable_timers ;;
esac
