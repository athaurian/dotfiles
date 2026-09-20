#!/bin/sh
# Restores the recorded wallpaper after apply. Runs only when this file
# changes. Normal applies leave the running session untouched.
[ -n "${WAYLAND_DISPLAY:-}" ] || exit 0
command -v "$HOME/.local/bin/sw" >/dev/null 2>&1 || exit 0
exec "$HOME/.local/bin/sw" --restore
