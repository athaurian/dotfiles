#!/usr/bin/env sh
set -eu

# Clipboard history picker via cliphist + fuzzel.
# Requires: cliphist, fuzzel, wl-copy/wl-paste.
# Bound to $mod+v in sway config.

if ! command -v cliphist >/dev/null 2>&1; then
	notify-send -u critical "clipboard" "cliphist not installed" 2>/dev/null || true
	exit 1
fi

if ! command -v fuzzel >/dev/null 2>&1; then
	notify-send -u critical "clipboard" "fuzzel not installed" 2>/dev/null || true
	exit 1
fi

# List history, pick with fuzzel, decode and copy.
# --dmenu mode lets fuzzel act as a picker.
selected=$(cliphist list | fuzzel --dmenu --placeholder "clipboard history..." --prompt " ") || exit 0
[ -z "$selected" ] && exit 0

printf '%s' "$selected" | cliphist decode | wl-copy
