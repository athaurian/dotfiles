#!/usr/bin/env sh
set -eu

# Bootstrap the systemd user session.
if ! command -v systemctl >/dev/null 2>&1; then
	exit 0
fi

systemctl --user import-environment \
	DISPLAY \
	XDG_SESSION_TYPE \
	XDG_CURRENT_DESKTOP \
	2>/dev/null || true
systemctl --user set-environment XDG_CURRENT_DESKTOP=i3 2>/dev/null || true

systemctl --user start --no-block graphical-session.target 2>/dev/null || true
systemctl --user start --no-block i3-session.target 2>/dev/null || true

# Polybar draws its own window; i3 has no bar section.
polybar main
