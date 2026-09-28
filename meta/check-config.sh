#!/bin/sh
# Validates the applied session configs with each WM's own validator. Only
# the machine running that WM has both the binary and the applied config
# (thinkpad: sway, optiplex: i3), so anything absent is skipped.
set -eu

check() {
	config=$1
	shift
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "check-config: skipped ($1 not installed)"
		return 0
	fi
	if [ ! -f "$config" ]; then
		echo "check-config: skipped ($config not present)"
		return 0
	fi
	"$@"
	echo "check-config: ok ($config)"
}

check "$HOME/.config/sway/config" sway -c "$HOME/.config/sway/config" --validate
check "$HOME/.config/i3/config" i3 -C -c "$HOME/.config/i3/config"
