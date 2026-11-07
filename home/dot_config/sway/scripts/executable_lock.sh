#!/usr/bin/env sh
set -eu

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

immediate=0
if [ "$#" -gt 0 ] && [ "$1" = "--now" ]; then
	immediate=1
	shift
fi

# Suspend waits for this script to return. This path shows no warning and
# has no delay.
if [ "$immediate" -eq 0 ]; then
	# Every dunst and notify call runs under a timeout to keep a hanging
	# daemon from blocking suspend.
	timeout 2 notify-send -a lock -u low -t 2500 " Locking screen..." || true
	sleep 2.5
fi

# Cleanup restores this level after unlock. A second locker must not save
# it, or it records the raised 100 and dunst stays paused after unlock.
pause_file="$(runtime_dir)/dunst_pause_before_lock"
pause_owner=0
if [ ! -f "$pause_file" ]; then
	timeout 2 dunstctl get-pause-level 2>/dev/null >"$pause_file" || echo 0 >"$pause_file"
	pause_owner=1
fi
timeout 2 dunstctl set-pause-level 100 2>/dev/null || true

lockimg="$(runtime_dir)/swaylock_bg_$$.png"
timeout 3 grim "$lockimg" 2>/dev/null || true

if command -v magick >/dev/null 2>&1; then
	timeout 3 magick "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 20% "$lockimg" 2>/dev/null || true
elif command -v convert >/dev/null 2>&1; then
	timeout 3 convert "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 20% "$lockimg" 2>/dev/null || true
fi

# Stop the unlocked unit so its idle timeout cannot lock again; cleanup
# swaps the units back.
systemctl --user start --no-block swayidle-locked.service || true
systemctl --user stop --no-block swayidle-unlocked.service || true

cleanup() {
	systemctl --user stop --no-block swayidle-locked.service || true
	systemctl --user start --no-block swayidle-unlocked.service || true
	if [ "$pause_owner" -eq 1 ]; then
		restore_level=0
		if [ -f "$pause_file" ]; then
			restore_level=$(state_digits "$(cat "$pause_file" 2>/dev/null || true)")
			[ -n "$restore_level" ] || restore_level=0
			rm -f "$pause_file"
		fi
		timeout 2 dunstctl set-pause-level "$restore_level" 2>/dev/null || true
		timeout 2 dunstctl close-all 2>/dev/null || true
	fi
	rm -f "$lockimg"
}

swaylock --image "$lockimg" "$@" &
lock_pid=$!
# Kill the locker on a signal. Then wait returns and cleanup runs.
trap 'pkill -x -u "$(id -u)" swaylock 2>/dev/null || true' TERM INT

if [ "$immediate" -eq 1 ]; then
	# Suspend waits for this script to return, so a background poller waits
	# for the unlock.
	(
		while kill -0 "$lock_pid" 2>/dev/null; do
			sleep 1
		done
		cleanup
	) &
else
	wait "$lock_pid" || true
	cleanup
fi
