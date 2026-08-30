#!/usr/bin/env sh
set -eu

# Bootstrap the systemd user session for Sway.
# Imports Wayland/session environment into the systemd user manager,
# then starts graphical-session.target and sway-session.target.
# Called once from sway config on compositor startup.

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

systemctl --user set-environment \
	XDG_CURRENT_DESKTOP=sway \
	2>/dev/null || true

# Start the standard graphical session target if it exists
systemctl --user start --no-block graphical-session.target 2>/dev/null || true

# Start the Sway-specific session target, which pulls in enabled services
systemctl --user start --no-block sway-session.target 2>/dev/null || true

# Session restore prompt (runs in background so it doesn't block startup)
"$HOME/.config/sway/scripts/session_restore_prompt.sh" &
