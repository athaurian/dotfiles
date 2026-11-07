#!/usr/bin/env sh
set -eu

if topgrade; then
	pkill -USR1 -f "^sh $HOME/.config/polybar/scripts/updates.sh$" || true
else
	status=$?
	printf 'topgrade failed with exit status %s\nPress Enter to close.\n' "$status"
	read -r _ || true
fi
