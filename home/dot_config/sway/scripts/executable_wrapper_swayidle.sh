#!/usr/bin/env sh
set -eu

# swayidle wrapper.

# Global timing policy (in seconds)
IDLE_LOCK=30
WARNING_OFFSET=10    # warning before lock
SCREEN_OFF_OFFSET=60 # screen turning off after lock
SUSPEND_OFFSET=10    # system suspending after screen off

SCRIPT_DIR="$HOME/.config/sway/scripts"

mode="${1:-}"

if [ "$mode" = "unlocked" ]; then
	IDLE_WARNING=$((IDLE_LOCK - WARNING_OFFSET))
	IDLE_SCREEN_OFF=$((IDLE_LOCK + SCREEN_OFF_OFFSET))
	IDLE_SUSPEND=$((IDLE_SCREEN_OFF + SUSPEND_OFFSET))

	warning_cmd="$SCRIPT_DIR/helper_idle_warning.sh $WARNING_OFFSET"
	resume_cmd="$SCRIPT_DIR/helper_idle_resume.sh"
	exec swayidle -w \
		timeout "$IDLE_WARNING" "$warning_cmd" \
		resume "$resume_cmd" \
		timeout "$IDLE_LOCK" "$SCRIPT_DIR/lock.sh" \
		timeout "$IDLE_SCREEN_OFF" 'swaymsg "output * power off"' \
		resume 'swaymsg "output * power on"' \
		timeout "$IDLE_SUSPEND" 'systemctl suspend' \
		before-sleep "$SCRIPT_DIR/lock.sh --now"

elif [ "$mode" = "locked" ]; then
	# When the screen locks, swayidle-locked starts. Time begins at 0.
	IDLE_SCREEN_OFF=$SCREEN_OFF_OFFSET
	IDLE_SUSPEND=$((IDLE_SCREEN_OFF + SUSPEND_OFFSET))

	exec swayidle -w \
		timeout "$IDLE_SCREEN_OFF" 'swaymsg "output * power off"' \
		resume 'swaymsg "output * power on"' \
		timeout "$IDLE_SUSPEND" 'systemctl suspend'

else
	echo "Usage: $0 <unlocked|locked>" >&2
	exit 1
fi
