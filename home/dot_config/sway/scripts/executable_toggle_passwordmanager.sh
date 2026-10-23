#!/usr/bin/env sh
set -eu

mark=keepassxc

. "$(dirname -- "$0")/lib_sway_lock.sh"
acquire_sway_lock "toggle_passwordmanager" || exit 0

has_mark() {
	swaymsg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	swaymsg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	release_sway_lock "toggle_passwordmanager"
	exit 0
fi

swaymsg exec "QT_QPA_PLATFORMTHEME=qt6ct exec ${PASSWORD_MANAGER:-keepassxc}"
release_sway_lock "toggle_passwordmanager"
