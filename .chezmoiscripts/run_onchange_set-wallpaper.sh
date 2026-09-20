#!/bin/sh
# Sets the desktop wallpaper for the locked theme. Runs on apply, but only
# when this file changes — point it at a new wallpaper and apply.
[ -n "${WAYLAND_DISPLAY:-}" ] || exit 0
command -v awww >/dev/null 2>&1 || exit 0
wallpaper="$HOME/Pictures/Wallpapers/neutral/flower-basket.jpg"
[ -f "$wallpaper" ] || exit 0
awww img "$wallpaper"
