#!/usr/bin/env sh
set -eu

# Bootstrap the systemd user session. Import the compositor environment
# first, then start the session targets.
if ! command -v systemctl >/dev/null 2>&1; then
	exit 0
fi

systemctl --user unset-environment SWAYSOCK
systemctl --user import-environment \
	DISPLAY \
	WAYLAND_DISPLAY \
	SWAYSOCK \
	XDG_SESSION_TYPE \
	XDG_CURRENT_DESKTOP \
	2>/dev/null || true
systemctl --user set-environment XDG_CURRENT_DESKTOP=sway 2>/dev/null || true

systemctl --user start --no-block graphical-session.target 2>/dev/null || true
systemctl --user start --no-block sway-session.target 2>/dev/null || true
