#!/bin/sh
# Validates the applied configs with each program's own checker. Every entry
# skips itself when the program is not installed or the config is not applied
# (the machine split keeps the other machine's files away from a machine).
#
# Configs without a native checker are deliberately absent: kitty, polybar,
# picom, dunst, waybar, swaylock, nvim, and the tool/app configs (btop, cava,
# fastfetch, lazygit, zathura, zellij, topgrade, gtk/qt) ship no check mode;
# refs/ pins the docs and CLI sources that establish this.
set -eu

failures=""

fail() { # fail PATH — collect and keep going, like refs/fetch-refs.sh
	failures="${failures}$1
"
}

check() { # check BINARY CONFIG COMMAND... — run the checker, collect failures
	bin=$1 config=$2
	shift 2
	if ! command -v "$bin" >/dev/null 2>&1; then
		echo "check-config: skipped $config ($bin not installed)"
		return 0
	fi
	if [ ! -f "$config" ]; then
		echo "check-config: skipped $config (not applied)"
		return 0
	fi
	if out=$("$@" 2>&1); then
		echo "check-config: ok $config"
	else
		echo "check-config: FAILED $config" >&2
		echo "$out" >&2
		fail "$config"
	fi
}

check sway "$HOME/.config/sway/config" \
	sway -c "$HOME/.config/sway/config" --validate
check i3 "$HOME/.config/i3/config" \
	i3 -C -c "$HOME/.config/i3/config"
check foot "$HOME/.config/foot/foot.ini" \
	foot --check-config --config "$HOME/.config/foot/foot.ini"
check fuzzel "$HOME/.config/fuzzel/fuzzel.ini" \
	fuzzel --check-config --config "$HOME/.config/fuzzel/fuzzel.ini"
check rofi "$HOME/.config/rofi/config.rasi" \
	rofi -rasi-validate "$HOME/.config/rofi/config.rasi"
check git "$HOME/.config/git/config" \
	git config --file "$HOME/.config/git/config" --list
check bash "$HOME/.bashrc" bash -n "$HOME/.bashrc"
check bash "$HOME/.bash_profile" bash -n "$HOME/.bash_profile"
check bash "$HOME/.bash_aliases" bash -n "$HOME/.bash_aliases"

# One verify over every deployed unit file. --man=no: verify otherwise fails
# on Documentation=man: entries whose page happens to be missing locally.
units_dir=$HOME/.config/systemd/user
if command -v systemd-analyze >/dev/null 2>&1 && [ -d "$units_dir" ]; then
	units=$(find "$units_dir" -maxdepth 1 -type f \
		\( -name '*.service' -o -name '*.target' -o -name '*.timer' \))
	if [ -n "$units" ]; then
		if out=$(systemd-analyze verify --man=no $units 2>&1); then
			echo "check-config: ok $units_dir"
		else
			echo "check-config: FAILED $units_dir" >&2
			echo "$out" >&2
			fail "$units_dir"
		fi
	fi
fi

[ -z "$failures" ] || exit 1
