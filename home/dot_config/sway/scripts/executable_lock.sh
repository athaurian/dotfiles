#!/usr/bin/env sh
set -eu

# Lock the screen with swaylock, managing swayidle lifecycle via systemd.
#
# Flags:
#   --now   Skip notification and delay, background swaylock (used by before-sleep)
#
# Called by: Super+Shift+x keybinding, swayidle timeout, before-sleep
# Dependencies: swaylock, grim, imagemagick (magick/convert), systemd, notify-send, makoctl

immediate=0
if [ "$#" -gt 0 ] && [ "$1" = "--now" ]; then
	immediate=1
fi

# --- Pre-lock notification (skipped with --now) ---
if [ "$immediate" -eq 0 ]; then
	# timeout prevents notify-send from hanging if mako is backlogged
	timeout 2 notify-send -u low -t 2500 " locking screen..." || true
	sleep 2.5
fi

# Suppress notifications while locked
# timeout is critical here, especially for --now (before-sleep), so a hanging
# mako instance doesn't prevent the system from suspending.
timeout 2 makoctl mode -a locked 2>/dev/null || true

# --- Capture and blur screenshot before locking ---
lockimg="$XDG_RUNTIME_DIR/swaylock_bg.png"
grim "$lockimg" 2>/dev/null || true

# Downscale to ~33% (360p), blur, and darken. Swaylock upscales the image.
# A 360p PNG instead of a full-res one saves CPU time and disk I/O.
if command -v magick >/dev/null 2>&1; then
	timeout 3 magick "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 10% "$lockimg" 2>/dev/null || true
elif command -v convert >/dev/null 2>&1; then
	timeout 3 convert "$lockimg" -scale 33% -blur 0x8 -fill black -colorize 10% "$lockimg" 2>/dev/null || true
fi

# --- Transition to locked idle state ---
# --no-block ensures systemd state changes don't delay the screen lock
systemctl --user start --no-block swayidle-locked.service || true
systemctl --user stop --no-block swayidle-unlocked.service || true

cleanup() {
	# --- Transition back to unlocked idle state ---
	systemctl --user stop --no-block swayidle-locked.service || true
	systemctl --user start --no-block swayidle-unlocked.service || true
	timeout 2 makoctl mode -r locked 2>/dev/null || true
	timeout 2 makoctl dismiss --all 2>/dev/null || true
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
