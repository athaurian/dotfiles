#!/usr/bin/env sh
set -eu

# The idle timeout, the before-sleep hook, and the lock keybinding all lock
# the screen through this script.

immediate=0
if [ "$#" -gt 0 ] && [ "$1" = "--now" ]; then
	immediate=1
fi

# The idle and manual paths warn before locking. The before-sleep path passes
# --now to skip the warning and the delay, because suspend waits for this
# script to return.
if [ "$immediate" -eq 0 ]; then
	# Every dunst and notify call runs under a timeout to keep a hanging
	# daemon from blocking suspend.
	timeout 2 notify-send -a lock -u low -t 2500 " Locking screen..." || true
	sleep 2.5
fi

# The current pause level is saved before this script raises it, and
# cleanup restores it after the unlock to put dunst back where it was.
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

# The unlocked unit must stop, or its idle timeout would lock the screen
# again. The locked unit arms only the screen-off and suspend timers, and
# cleanup swaps the units back when swaylock exits.
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
	swaylock --image "$lockimg" &
	lock_pid=$!
	(
		while kill -0 "$lock_pid" 2>/dev/null; do
			sleep 1
		done
		cleanup
	) &
else
	swaylock --image "$lockimg"
	cleanup
fi
