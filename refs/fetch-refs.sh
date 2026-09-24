#!/usr/bin/env sh
# Restore the refs/ material that was deleted from the committed tree because
# it is reproducible in one command per entry: upstream clones pinned to the
# commits they were last read at, man-page/doc fetches, the pinned polybar doc
# subset, and the pre-reset bundle regenerated from local git history.
#
# Committed refs/ entries (findings, handoff, zellij-themes) are not touched.
#
# Usage: sh refs/fetch-refs.sh [target-dir]
#   target-dir defaults to this script's own directory (refs/).
#   Existing entries are skipped, so re-running is safe.
set -eu

target=${1:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$target"

fetch() { # fetch URL RELATIVE-PATH
	url=$1 path=$2
	[ -f "$target/$path" ] && return 0
	mkdir -p "$target/$(dirname "$path")"
	curl -fsSL "$url" -o "$target/$path"
}

clone() { # clone URL RELATIVE-PATH COMMIT
	url=$1 path=$2 sha=$3
	[ -d "$target/$path/.git" ] || git clone -q "$url" "$target/$path"
	git -C "$target/$path" checkout -q "$sha" 2>/dev/null ||
		echo "fetch-refs: $path: $sha unreachable upstream, kept default branch" >&2
}

# Reference clones, pinned to the commits they were last read at.
clone https://github.com/catppuccin/nvim catppuccin-nvim edefef779ab08ce1a4a404713e3012b0d202bd35
clone https://github.com/folke/lazy.nvim lazy-nvim 306a05526ada86a7b30af95c5cc81ffba93fef97
clone https://github.com/williamboman/mason.nvim mason-nvim 2a6940af80375532e5e9e7c1f2fc6319a1b7a69d
clone https://github.com/Binaryify/OneDark-Pro onedark-pro 54c3280b29f2c2ed9751e5ca4e071380b7b42205
clone https://github.com/folke/snacks.nvim snacks-nvim 882c996cf28183f4d63640de0b4c02ec886d01f2
clone https://github.com/polybar/polybar.wiki.git polybar-wiki b4f3c9e9108741bd34e4d02b2e8fa40046cb0c65

# Man pages and upstream doc snapshots.
fetch https://raw.githubusercontent.com/yshui/picom/next/picom.sample.conf picom/picom.sample.conf
fetch https://raw.githubusercontent.com/davatorium/rofi/next/doc/rofi.1.markdown rofi/rofi.1.markdown
fetch https://raw.githubusercontent.com/davatorium/rofi/next/doc/rofi-theme.5.markdown rofi/rofi-theme.5.markdown
fetch https://raw.githubusercontent.com/davatorium/rofi/next/doc/default_configuration.rasi rofi/default_configuration.rasi
fetch https://raw.githubusercontent.com/davatorium/rofi/next/doc/default_theme.rasi rofi/default_theme.rasi
fetch https://raw.githubusercontent.com/i3/i3/next/man/i3.man i3/i3.man
fetch https://raw.githubusercontent.com/i3/i3/next/man/i3-msg.man i3/i3-msg.man
fetch https://i3wm.org/docs/userguide.html i3/userguide.html
fetch https://raw.githubusercontent.com/Raymo111/i3lock-color/master/i3lock.1 i3lock-color/i3lock.1
fetch https://raw.githubusercontent.com/jonls/redshift/master/redshift.1 redshift/redshift.1

# Polybar doc subset from the pinned commit (also the source of the /tmp
# scratch tree cited in polybar-migration-findings.md).
if [ ! -f "$target/polybar/polybar.1.rst" ]; then
	polybar_sha=b3af5a33166604c689705d7dc67b69c01482d707
	tmp=$(mktemp -d)
	curl -fsSL "https://github.com/polybar/polybar/archive/$polybar_sha.tar.gz" | tar xz -C "$tmp"
	mkdir -p "$target/polybar"
	cp "$tmp/polybar-$polybar_sha/doc/man/polybar.1.rst" \
		"$tmp/polybar-$polybar_sha/doc/man/polybar.5.rst" \
		"$tmp/polybar-$polybar_sha/doc/user/modules/tray.rst" \
		"$target/polybar/"
	rm -rf "$tmp"
fi

# Pre-reset history snapshot; regenerable because the local
# backup/pre-reset-2567b2d branch still holds the identical objects.
if [ ! -f "$target/dotfiles-pre-reset.bundle" ]; then
	git -C "$repo" bundle create "$target/dotfiles-pre-reset.bundle" backup/pre-reset-2567b2d
fi
