#!/usr/bin/env sh
set -eu

topgrade || true
pkill -USR1 -f "^sh $HOME/.config/polybar/scripts/updates.sh$" || true
