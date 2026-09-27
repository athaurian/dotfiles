#!/usr/bin/env sh
# Restore the refs/ material that is not committed because it is reproducible
# in one command per entry: upstream clones and full source trees pinned to
# the commits the findings cite, man-page/doc fetches pinned to the same
# commits, and the pre-reset bundle regenerated from local git history.
#
# The committed refs/ entries (this script, .gitignore, the handoff, the
# findings, zellij-themes) are never touched, and refs/.gitignore keeps
# everything restored here out of `git status`.
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

source_tree() { # source_tree NAME TARBALL-URL
	name=$1 url=$2
	dest=$target/src/$name
	# The recorded tarball URL doubles as the pin: editing it refreshes.
	[ -f "$dest/.source" ] && [ "$(cat "$dest/.source")" = "$url" ] && return 0
	rm -rf "$dest"
	mkdir -p "$dest"
	curl -fsSL "$url" | tar xz --strip-components=1 -C "$dest"
	printf '%s\n' "$url" >"$dest/.source"
}

# Reference clones, pinned to the commits they were last read at. The chezmoi
# clone carries the template/syntax reference under assets/chezmoi.io/docs/;
# the waybar wiki is the porting source of truth for the bar migration.
clone https://github.com/catppuccin/nvim catppuccin-nvim edefef779ab08ce1a4a404713e3012b0d202bd35
clone https://github.com/folke/lazy.nvim lazy-nvim 306a05526ada86a7b30af95c5cc81ffba93fef97
clone https://github.com/williamboman/mason.nvim mason-nvim 2a6940af80375532e5e9e7c1f2fc6319a1b7a69d
clone https://github.com/Binaryify/OneDark-Pro onedark-pro 54c3280b29f2c2ed9751e5ca4e071380b7b42205
clone https://github.com/folke/snacks.nvim snacks-nvim 882c996cf28183f4d63640de0b4c02ec886d01f2
wiki_sha=b4f3c9e9108741bd34e4d02b2e8fa40046cb0c65
clone https://github.com/polybar/polybar.wiki.git polybar-wiki "$wiki_sha"
clone https://github.com/twpayne/chezmoi chezmoi 593166436bf621259efb33d12ebeecd7bae17329
clone https://github.com/Alexays/Waybar.wiki.git waybar-wiki c9b404b7297254c1948fc65517a87d7110881b2c

# Full source trees for the exact commits cited as proof in
# polybar-migration-findings.md (parser-specs/, bindings.c, units.cpp, …).
source_tree i3 "https://github.com/i3/i3/archive/903bcd518df32b0e055b17f5da3f988a0187fd3d.tar.gz"
source_tree polybar "https://github.com/polybar/polybar/archive/b3af5a33166604c689705d7dc67b69c01482d707.tar.gz"

# Doc copies derived from those trees (same pins, no second source of truth);
# the rendered userguide.html is the only artifact not in the tree and tracks
# the latest i3 release rather than the pin.
if [ ! -f "$target/i3/i3.man" ]; then
	mkdir -p "$target/i3"
	cp "$target/src/i3/man/i3.man" "$target/src/i3/man/i3-msg.man" "$target/i3/"
fi
fetch https://i3wm.org/docs/userguide.html i3/userguide.html
if [ ! -f "$target/polybar/polybar.1.rst" ]; then
	mkdir -p "$target/polybar"
	cp "$target/src/polybar/doc/man/polybar.1.rst" \
		"$target/src/polybar/doc/man/polybar.5.rst" \
		"$target/src/polybar/doc/user/modules/tray.rst" \
		"$target/polybar/"
fi
if [ ! -f "$target/polybar/default-config.ini" ]; then
	mkdir -p "$target/polybar"
	cp "$target/src/polybar/doc/config.ini" "$target/polybar/default-config.ini"
fi

# Flat copies of the wiki pages the bar config uses, at the same pin as
# the polybar-wiki clone; names match the curated refs/polybar/ layout.
for page in i3 script text ipc cpu memory date pulseaudio xworkspaces; do
	fetch "https://raw.githubusercontent.com/polybar/polybar.wiki/$wiki_sha/Module:-$page.md" "polybar/module-$page.md"
done
for page in Configuration Formatting; do
	fetch "https://raw.githubusercontent.com/polybar/polybar.wiki/$wiki_sha/$page.md" "polybar/$page.md"
done

# Wayland side (thinkpad): compositor, locker, bar, launchers, capture,
# wallpaper, colour temperature.
sway_sha=1652c54b73f67df17b7b4ab0b0f7048204aa8104
for page in sway.1.scd sway.5.scd sway-bar.5.scd sway-input.5.scd sway-output.5.scd sway-ipc.7.scd; do
	fetch "https://raw.githubusercontent.com/swaywm/sway/$sway_sha/sway/$page" "sway/$page"
done
fetch "https://raw.githubusercontent.com/swaywm/sway/$sway_sha/swaymsg/swaymsg.1.scd" sway/swaymsg.1.scd
fetch "https://raw.githubusercontent.com/wlrfx/swayfx/972e98614168a3a79ae1a84f59baa5001639e15f/README.md" swayfx/README.md
fetch "https://raw.githubusercontent.com/swaywm/swaylock/44b82de635c3bc66b0093abd1cf8cc1c8b1b9c0f/swaylock.1.scd" swaylock/swaylock.1.scd
# The Arch package is jirutka's maintained fork (AUR upstream), not mortie's.
fetch "https://raw.githubusercontent.com/jirutka/swaylock-effects/496059a8565c2d5eed672c2e5bc5e1edd14b3de8/README.md" swaylock-effects/README.md
fetch "https://raw.githubusercontent.com/swaywm/swayidle/a959e59c64b55dd17a974dda4c4b71dff520af3a/swayidle.1.scd" swayidle/swayidle.1.scd
fuzzel_sha=616485c08cd0924af23f0ee9cbf7f104baba2dcc
for page in fuzzel.1.scd fuzzel.ini.5.scd; do
	fetch "https://codeberg.org/dnkl/fuzzel/raw/commit/$fuzzel_sha/doc/$page" "fuzzel/$page"
done
foot_sha=9f5c70ea6eed64706471ea3ca349181a77f21c66
for page in foot.1.scd foot.ini.5.scd; do
	fetch "https://codeberg.org/dnkl/foot/raw/commit/$foot_sha/doc/$page" "foot/$page"
done
fetch "https://raw.githubusercontent.com/emersion/grim/47e2658619c6b5a790732c5876fb84e8273f08a9/grim.1.scd" grim/grim.1.scd
fetch "https://raw.githubusercontent.com/emersion/slurp/a3998d3ec79fbd85b81911f43010466b032ed0d9/slurp.1.scd" slurp/slurp.1.scd
fetch "https://raw.githubusercontent.com/Satty-org/Satty/2bcd9111390a7ae03ef965e87a6a12dfd22bf93b/README.md" satty/README.md
wlsunset_sha=0c8cc663d085388fa59efb7cbea8df8c8234c562
fetch "https://raw.githubusercontent.com/kennylevinsen/wlsunset/$wlsunset_sha/README.md" wlsunset/README.md
fetch "https://raw.githubusercontent.com/kennylevinsen/wlsunset/$wlsunset_sha/wlsunset.1.scd" wlsunset/wlsunset.1.scd
awww_sha=25ea4fd7a42359379da9ddadedda1c477caa4ae0
for page in awww awww-clear awww-clear-cache awww-daemon awww-img awww-kill awww-pause awww-query awww-restore; do
	fetch "https://codeberg.org/LGFae/awww/raw/commit/$awww_sha/doc/$page.1.scd" "awww/$page.1.scd"
done

# X11 side (optiplex): compositor, bar, launcher, locker, idle, capture.
rofi_sha=7575b70967c6ea747ecdeb4e54dc88fbf3939e6d
for page in rofi.1.markdown rofi-theme.5.markdown rofi-script.5.markdown default_configuration.rasi default_theme.rasi; do
	fetch "https://raw.githubusercontent.com/davatorium/rofi/$rofi_sha/doc/$page" "rofi/$page"
done
picom_sha=3502b29b8316c368229c25646dde6aff978bab67
fetch "https://raw.githubusercontent.com/yshui/picom/$picom_sha/picom.sample.conf" picom/picom.sample.conf
fetch "https://raw.githubusercontent.com/yshui/picom/$picom_sha/man/picom.1.adoc" picom/picom.1.adoc
dunst_sha=df50df4bb2ec4f8b8aef0b837644fa93274b0863
for page in dunst.1.pod.in dunst.5.pod dunstctl.pod dunstify.pod; do
	fetch "https://raw.githubusercontent.com/dunst-project/dunst/$dunst_sha/docs/$page" "dunst/$page"
done
fetch "https://raw.githubusercontent.com/Raymo111/i3lock-color/e6c0caf9b7aa22cc7864493132a1a2e258da1761/i3lock.1" i3lock-color/i3lock.1
fetch "https://raw.githubusercontent.com/jonls/redshift/490ba2aae9cfee097a88b6e2be98aeb1ce990050/redshift.1" redshift/redshift.1
# gitlab.freedesktop.org serves a login page anonymously; this GitHub mirror
# keeps the doc/ files (xss-lock.1, transfer-sleep-lock-i3lock.sh) the fd
# contract in lock.sh is written against.
xss_lock_sha=cd0b89df9bac1880ea6ea830251c6b4492d505a5
fetch "https://raw.githubusercontent.com/xdbob/xss-lock/$xss_lock_sha/doc/xss-lock.1.rst.in" xss-lock/xss-lock.1.rst.in
fetch "https://raw.githubusercontent.com/xdbob/xss-lock/$xss_lock_sha/doc/transfer-sleep-lock-i3lock.sh" xss-lock/transfer-sleep-lock-i3lock.sh
fetch "https://raw.githubusercontent.com/derf/feh/4852b6f8b47f2b31be2b46851b43ab772defdefa/man/feh.pre" feh/feh.pre
fetch "https://raw.githubusercontent.com/flameshot-org/flameshot/2d478061ffeeba5919d3a3d9168f93542ea9b357/README.md" flameshot/README.md

# Shared config surfaces: terminals, apps, and services with repo-owned
# configs (data/packages.json) or invoked by repo scripts.
fetch "https://raw.githubusercontent.com/kovidgoyal/kitty/f03c45419681e3027ecb871defcf06dd1c08234b/docs/conf.rst" kitty/conf.rst
zathura_sha=4fad4e4d82ac3275632fcbc55386915ff361e404
fetch "https://raw.githubusercontent.com/pwmt/zathura/$zathura_sha/doc/man/zathura.1.rst" zathura/zathura.1.rst
fetch "https://raw.githubusercontent.com/pwmt/zathura/$zathura_sha/doc/man/zathurarc.5.rst" zathura/zathurarc.5.rst
fetch "https://raw.githubusercontent.com/aristocratos/btop/612e18f5bd598fe987b30d041b39e5d7b3e0794f/README.md" btop/README.md
cava_sha=299219826379e137f0f4c48bfdc96019360964ec
fetch "https://raw.githubusercontent.com/karlstav/cava/$cava_sha/example_files/config" cava/config
fetch "https://raw.githubusercontent.com/karlstav/cava/$cava_sha/README.md" cava/README.md
fastfetch_sha=bba45429ae15aa0ce55f351c98abea8f53715982
fetch "https://raw.githubusercontent.com/fastfetch-cli/fastfetch/$fastfetch_sha/doc/fastfetch.1.in" fastfetch/fastfetch.1.in
fetch "https://raw.githubusercontent.com/fastfetch-cli/fastfetch/$fastfetch_sha/doc/json_schema.json" fastfetch/json_schema.json
lazygit_sha=5fcbdadc67dc6bb8b60d2c095306d9ba21bc62c6
fetch "https://raw.githubusercontent.com/jesseduffield/lazygit/$lazygit_sha/docs/Config.md" lazygit/Config.md
fetch "https://raw.githubusercontent.com/jesseduffield/lazygit/$lazygit_sha/docs/keybindings/Keybindings_en.md" lazygit/Keybindings_en.md
fetch "https://raw.githubusercontent.com/topgrade-rs/topgrade/14c3f001d14a6304acdf015ed908f004931354d5/README.md" topgrade/README.md
fetch "https://raw.githubusercontent.com/altdesktop/playerctl/b19a71cb9dba635df68d271bd2b3f6a99336a223/README.md" playerctl/README.md
# Session-target/timer/EnvironmentFile semantics for home/dot_config/systemd.
systemd_sha=1cf66d1c674ce5928f5b2709629afeaaaf79aee2
for page in systemd.unit systemd.service systemd.exec systemd.timer systemd.special; do
	fetch "https://raw.githubusercontent.com/systemd/systemd/$systemd_sha/man/$page.xml" "systemd/$page.xml"
done

# Pre-reset history snapshot; regenerable because the local
# backup/pre-reset-2567b2d branch still holds the identical objects. The
# branch can be absent on a given machine, so machines without it skip the
# bundle instead of failing the run.
if [ ! -f "$target/dotfiles-pre-reset.bundle" ]; then
	if git -C "$repo" rev-parse --verify --quiet backup/pre-reset-2567b2d >/dev/null; then
		git -C "$repo" bundle create "$target/dotfiles-pre-reset.bundle" backup/pre-reset-2567b2d
	else
		echo "fetch-refs: backup/pre-reset-2567b2d absent here, skipping dotfiles-pre-reset.bundle" >&2
	fi
fi
