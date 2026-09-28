#!/bin/sh
# Restart the tray applets as a single instance: i3 runs this from
# exec_always (startup/restart only) and the gtk-mode hook runs it after a
# reload, so killing first keeps every path idempotent. Applets resolve the
# current icon theme when they start.

set -eu

pkill -x blueman-applet >/dev/null 2>&1 || true
pkill -x nm-applet >/dev/null 2>&1 || true
sleep 0.3
(setsid blueman-applet >/dev/null 2>&1 < /dev/null &) || true
(setsid nm-applet --indicator >/dev/null 2>&1 < /dev/null &) || true
