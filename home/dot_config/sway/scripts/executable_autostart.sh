#!/usr/bin/env sh
set -eu

# Hand the Wayland session environment to the user manager, then start
# graphical-session.target and sway-session.target. Wayland-dependent
# services live in sway-session.target.wants/ and cannot start before
# the compositor environment exists.
systemctl --user import-environment \
	WAYLAND_DISPLAY \
	SWAYSOCK \
	XDG_SESSION_TYPE \
	XDG_CURRENT_DESKTOP

systemctl --user start --no-block graphical-session.target 2>/dev/null || true
systemctl --user start --no-block sway-session.target 2>/dev/null || true
