#!/usr/bin/env sh
set -eu

# Runs inside the topgrade terminal (kitty instance topgrade_term).
# When topgrade exits, SIGUSR1 the updates module's tail script so the
# count refreshes at once instead of after its 600s loop (the pattern
# anchors on the script's exact cmdline, not on stray editors).
# The poke must happen even when topgrade fails, hence `|| true`.

topgrade || true
pkill -USR1 -f "^sh $HOME/.config/polybar/scripts/updates.sh$" || true
