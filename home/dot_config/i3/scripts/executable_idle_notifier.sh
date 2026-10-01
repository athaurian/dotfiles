#!/usr/bin/env sh
set -eu

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

nid=$(timeout 2 dunstify -a idle-warning -u low -t "${cycle}000" -p '󰂠 Idle warning' "Screen locking in ${cycle}s." 2>/dev/null || true)
nid=$(printf '%s' "$nid" | tr -cd '0-9')

while :; do
	sleep 1 &
	wait $! || true
done
