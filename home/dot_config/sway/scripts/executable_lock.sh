#!/usr/bin/env sh
set -eu

immediate=0
if [ "$#" -gt 0 ] && [ "$1" = "--now" ]; then
	immediate=1
	shift
fi

# Suspend waits for this script to return, so the before-sleep path skips
# the warning and the delay.
if [ "$immediate" -eq 0 ]; then
	# Every dunst and notify call runs under a timeout to keep a hanging
	# daemon from blocking suspend.
	timeout 2 notify-send -a lock -u low -t 2500 " Locking screen..." || true
	sleep 2.5
fi

# Saved so cleanup can restore the level after unlock.
pause_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_pause_before_lock"
timeout 2 dunstctl get-pause-level 2>/dev/null >"$pause_file" || echo 0 >"$pause_file"
timeout 2 dunstctl set-pause-level 100 2>/dev/null || true

lockimg="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/swaylock_bg.png"
grim "$lockimg" 2>/dev/null || true

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
	pause_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_pause_before_lock"
	restore_level=0
	if [ -f "$pause_file" ]; then
		restore_level=$(tr -cd '0-9' <"$pause_file" 2>/dev/null || true)
		[ -n "$restore_level" ] || restore_level=0
		rm -f "$pause_file"
	fi
	timeout 2 dunstctl set-pause-level "$restore_level" 2>/dev/null || true
	timeout 2 dunstctl close-all 2>/dev/null || true
	rm -f "$lockimg"
}

if [ "$immediate" -eq 1 ]; then
	swaylock --image "$lockimg" "$@" &
	lock_pid=$!
	(
		while kill -0 "$lock_pid" 2>/dev/null; do
			sleep 1
		done
		cleanup
	) &
else
	swaylock --image "$lockimg" "$@"
	cleanup
fi
