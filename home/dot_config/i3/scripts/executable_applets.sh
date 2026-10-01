#!/bin/sh

set -eu

pkill -x blueman-applet >/dev/null 2>&1 || true
pkill -x nm-applet >/dev/null 2>&1 || true
sleep 0.3
(setsid blueman-applet >/dev/null 2>&1 < /dev/null &) || true
(setsid nm-applet --indicator >/dev/null 2>&1 < /dev/null &) || true
