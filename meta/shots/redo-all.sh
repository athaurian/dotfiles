#!/usr/bin/env sh
set -eu

ROOT=$(cd "$(dirname -- "$0")/../.." && pwd -P)
cd "$ROOT"

restore() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$(cat "$HOME/.local/state/palette-mode" 2>/dev/null || echo dark)" != dark ]; then
		"$HOME/.local/bin/palette-mode" dark >/dev/null 2>&1 || true
	fi
	swaymsg workspace 1 >/dev/null 2>&1 || true
	exit "$status"
}
trap restore EXIT HUP INT TERM

printf 'Clearing old captures\n'
rm -f \
	meta/captures/stage-light.png \
	meta/captures/stage-dark.png \
	meta/captures/empty-light.png \
	meta/captures/empty-dark.png \
	meta/captures/menu-launcher-light.png \
	meta/captures/menu-launcher.png \
	meta/captures/menu-poweroff-light.png \
	meta/captures/menu-poweroff.png \
	meta/captures/picker-clipboard-light.png \
	meta/captures/picker-clipboard.png \
	meta/captures/bar-light.png \
	meta/captures/bar-dark.png \
	meta/captures/editor-light.png \
	meta/captures/editor-dark.png

printf 'Light captures\n'
meta/shots/hero.py light
meta/shots/empty.py light
meta/shots/pickers.py light
meta/shots/clipboard.py light
meta/shots/bar.py light
meta/shots/editor.py light

printf 'Dark captures\n'
meta/shots/hero.py dark
meta/shots/empty.py dark
meta/shots/pickers.py dark
meta/shots/clipboard.py dark
meta/shots/bar.py dark
meta/shots/editor.py dark

printf 'Compose\n'
meta/shots/hero.py compose
meta/shots/empty.py compose
meta/shots/editor.py compose
meta/shots/palette.py

printf 'Social image\n'
make social
