#!/usr/bin/env sh
set -eu

ROOT=$(cd "$(dirname -- "$0")/../.." && pwd -P)
cd "$ROOT"

mode_before=$(cat "$HOME/.local/state/palette-mode" 2>/dev/null || echo dark)
case "$mode_before" in
dark | light) ;;
*) mode_before=dark ;;
esac
workspace_before=$(swaymsg -t get_workspaces | jq -r '.[] | select(.focused) | .name')

restore() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$(cat "$HOME/.local/state/palette-mode" 2>/dev/null || echo dark)" != "$mode_before" ]; then
		"$HOME/.local/bin/palette-mode" "$mode_before" >/dev/null 2>&1 || true
	fi
	if [ -n "$workspace_before" ]; then
		swaymsg workspace "$workspace_before" >/dev/null 2>&1 || true
	fi
	exit "$status"
}
trap restore EXIT HUP INT TERM

printf 'Clearing old captures\n'
rm -f \
	meta/captures/stage-light.png \
	meta/captures/stage-dark.png \
	meta/captures/stage-launcher-light.png \
	meta/captures/stage-launcher.png \
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
