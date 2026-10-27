#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
cd "$ROOT"

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
meta/shots/editor.py dark

printf 'Editor light\n'
meta/shots/editor.py light
printf 'Editor compose\n'
meta/shots/editor.py compose

printf 'Palette card\n'
meta/shots/palette.py

printf 'Social image\n'
make social

printf 'Restore session\n'
~/.local/bin/palette-mode dark
swaymsg workspace 1 >/dev/null
