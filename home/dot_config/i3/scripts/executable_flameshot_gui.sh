#!/usr/bin/env sh
set -eu

# Flameshot region capture. Bound to Shift+Print.
# -c also copies the capture, matching the sway path's clipboard copy.

save_dir="$HOME/Pictures/Screenshots"
mkdir -p "$save_dir"

flameshot gui -p "$save_dir" -c
