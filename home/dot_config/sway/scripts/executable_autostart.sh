#!/usr/bin/env sh
set -eu

# Import Wayland env, start session targets. Wayland services need the compositor env first.
systemctl --user import-environment \
	WAYLAND_DISPLAY \
	SWAYSOCK \
	XDG_SESSION_TYPE \
	XDG_CURRENT_DESKTOP

systemctl --user start --no-block graphical-session.target 2>/dev/null || true
systemctl --user start --no-block sway-session.target 2>/dev/null || true
