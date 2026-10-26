#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
cd "$ROOT"

SHOT_TMP=/tmp/chezmoi-shots
EDITOR_SOCK="$SHOT_TMP/editor.sock"

stop_editor() {
	local pid
	pid=$(swaymsg -t get_tree |
		jq -r '.. | objects | select(.app_id? == "editor-nvim") | .pid' |
		head -n 1)
	if [ -n "${pid:-}" ]; then
		kill -TERM "$pid" 2>/dev/null || true
		for _ in $(seq 1 20); do
			kill -0 "$pid" 2>/dev/null || break
			sleep 0.1
		done
		kill -KILL "$pid" 2>/dev/null || true
	fi
	rm -f "$EDITOR_SOCK"
}

start_editor() {
	stop_editor
	swaymsg workspace 3 >/dev/null
	swaymsg exec "sh -c 'cd $ROOT && exec kitty --class editor-nvim nvim --listen $EDITOR_SOCK +330 assets/hl_test.py'" >/dev/null
	for _ in $(seq 1 100); do
		if swaymsg -t get_tree |
			jq -e '.. | objects | select(.app_id? == "editor-nvim")' >/dev/null
		then
			break
		fi
		sleep 0.1
	done
	for _ in $(seq 1 100); do
		[ -S "$EDITOR_SOCK" ] && break
		sleep 0.1
	done
	sleep 11
	for _ in $(seq 1 3); do
		timeout 5 nvim --server "$EDITOR_SOCK" --remote-send '<Esc><CR>' >/dev/null || true
		sleep 1
	done
	timeout 5 nvim --server "$EDITOR_SOCK" --remote-send ':lua Snacks.explorer()<CR>' >/dev/null
	sleep 1.5
	timeout 5 nvim --server "$EDITOR_SOCK" --remote-send 'I' >/dev/null
	sleep 1.5
	timeout 5 nvim --server "$EDITOR_SOCK" --remote-send '<C-w>l330Gzz' >/dev/null
	sleep 0.5

	local buffer lines line
	buffer=$(timeout 5 nvim --server "$EDITOR_SOCK" --remote-expr 'expand("%:p")')
	lines=$(timeout 5 nvim --server "$EDITOR_SOCK" --remote-expr 'line("$")')
	line=$(timeout 5 nvim --server "$EDITOR_SOCK" --remote-expr 'line(".")')
	if [ "$buffer" != "$ROOT/assets/hl_test.py" ] || [ "$lines" -lt 100 ] || [ "$line" -ne 330 ]; then
		printf 'editor setup failed: %s, %s lines, cursor %s\n' \
			"$buffer" "$lines" "$line" >&2
		exit 1
	fi
}

stop_editor

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
rm -f \
	docs/images/hero.webp \
	docs/images/hero-empty.webp \
	docs/images/og.png \
	docs/images/picker-launcher.webp \
	docs/images/picker-launcher-light.webp \
	docs/images/picker-poweroff.webp \
	docs/images/picker-poweroff-light.webp \
	docs/images/picker-clipboard.webp \
	docs/images/picker-clipboard-light.webp \
	docs/images/bar.webp \
	docs/images/bar-light.webp \
	docs/images/neovim-editor.webp \
	docs/images/neovim-editor-light.webp \
	docs/images/palette.webp

printf 'Hero light\n'
meta/shots/hero.py light
printf 'Hero dark\n'
meta/shots/hero.py dark
printf 'Hero compose\n'
meta/shots/hero.py compose

printf 'Empty light\n'
meta/shots/empty.py light
printf 'Empty dark\n'
meta/shots/empty.py dark
printf 'Empty compose\n'
meta/shots/empty.py compose

printf 'Pickers dark\n'
meta/shots/pickers.py dark
printf 'Pickers light\n'
meta/shots/pickers.py light

printf 'Clipboard dark\n'
meta/shots/clipboard.py dark
printf 'Clipboard light\n'
meta/shots/clipboard.py light

printf 'Bar dark\n'
meta/shots/bar.py dark
printf 'Bar light\n'
meta/shots/bar.py light

printf 'Editor dark\n'
~/.local/bin/palette-mode dark
start_editor
meta/shots/editor.py dark
stop_editor

printf 'Editor light\n'
~/.local/bin/palette-mode light
start_editor
meta/shots/editor.py light
stop_editor
printf 'Editor compose\n'
meta/shots/editor.py compose

printf 'Palette card\n'
meta/shots/palette.py

printf 'Social image\n'
make social

printf 'Restore session\n'
~/.local/bin/palette-mode dark
swaymsg workspace 1 >/dev/null
