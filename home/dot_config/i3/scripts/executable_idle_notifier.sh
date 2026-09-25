#!/usr/bin/env sh
set -eu

# xss-lock --notifier: the pre-lock countdown notice on the idle path
# (X11 twin of sway's helper_idle_warning.sh). xss-lock runs this when the
# screensaver activates on inactivity, starts the locker after the xset
# cycle, and signals us in between: SIGHUP when the user is active again,
# SIGTERM when the locker starts. The cycle is therefore the remaining
# time until the lock; a zero cycle never runs this script.

cycle=$(xset q 2>/dev/null | sed -n 's/.*cycle: *\([0-9][0-9]*\).*/\1/p' | head -n 1)
case "$cycle" in
"" | 0) exit 0 ;;
esac

nid=""

close_notice() {
	if [ -n "$nid" ]; then
		dunstctl close "$nid" 2>/dev/null || true
	fi
	exit 0
}

trap 'close_notice' HUP TERM

# Timeout avoids hangs on backlogged dunst; -a matches idle-warning.
nid=$(timeout 2 dunstify -a idle-warning -u low -t "${cycle}000" -p '󰂠 idle warning' "screen locking in ${cycle}s" 2>/dev/null || true)
nid=$(printf '%s' "$nid" | tr -cd '0-9')

# Stay alive so xss-lock can signal us; the notice also self-expires
# at lock time via its timeout.
while :; do
	sleep 1 &
	wait $! || true
done
