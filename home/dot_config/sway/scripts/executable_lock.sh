#!/usr/bin/env sh
set -eu

# Lock the screen with swaylock, managing swayidle lifecycle via systemd.
#
# Flags:
#   --now   Skip notification and delay, background swaylock (used by before-sleep)
#
# Called by: Super+Shift+x keybinding, swayidle timeout, before-sleep
# This script needs swaylock, grim, imagemagick, systemd, notify-send, and dunstctl. For imagemagick use magick or convert.

immediate=0
if [ "$#" -gt 0 ] && [ "$1" = "--now" ]; then
	immediate=1
fi

# --- Pre-lock notification (skipped with --now) ---
if [ "$immediate" -eq 0 ]; then
	# timeout prevents notify-send from hanging if dunst is backlogged.
	# -a lock matches the dnd_bypass_lock rule so this still shows during DND.
	timeout 2 notify-send -a lock -u low -t 2500 " locking screen..." || true
	sleep 2.5
fi

# Suppress notifications while locked at the maximum pause level, which
# hides even the DND-bypass script notices (their override is 90).
# Save the current level so unlock restores DND instead of clearing it.
# timeout is critical here, especially for --now (before-sleep), so a hanging
# dunst instance doesn't prevent the system from suspending.
pause_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dunst_pause_before_lock"
timeout 2 dunstctl get-pause-level 2>/dev/null >"$pause_file" || echo 0 >"$pause_file"
timeout 2 dunstctl set-pause-level 100 2>/dev/null || true

# --- Capture and blur screenshot before locking ---
lockimg="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/swaylock_bg.png"
grim "$lockimg" 2>/dev/null || true

# Downscale to ~33% (360p), blur, and darken. Swaylock upscales the image.
# A 360p PNG instead of a full-res one saves CPU time and disk I/O.
if command -v magick >/dev/null 2>&1; then
	timeout 3 magick "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 20% "$lockimg" 2>/dev/null || true
elif command -v convert >/dev/null 2>&1; then
	timeout 3 convert "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 20% "$lockimg" 2>/dev/null || true
fi

# --- Transition to locked idle state ---
# --no-block ensures systemd state changes don't delay the screen lock
systemctl --user start --no-block swayidle-locked.service || true
systemctl --user stop --no-block swayidle-unlocked.service || true

cleanup() {
	# --- Transition back to unlocked idle state ---
	systemctl --user stop --no-block swayidle-locked.service || true
	systemctl --user start --no-block swayidle-unlocked.service || true
	# Restore the pre-lock pause level (usually DND or 0) instead of
	# blindly unpausing, so locking with DND on keeps DND on.
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
