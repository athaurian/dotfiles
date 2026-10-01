#!/usr/bin/env sh
set -eu

save_dir="$HOME/Pictures/Screenshots"
mkdir -p "$save_dir"

flameshot gui -p "$save_dir" -c
