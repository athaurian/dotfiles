# Installation

## Prerequisites

- Arch Linux with `bash` and systemd user services, CachyOS preferred
- A hostname of `thinkpad` or `optiplex`, because the hostname selects the
  entries that
  [`.chezmoiignore`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoiignore)
  skips and the machine's package list in
  [`data/packages.json`](https://github.com/athaurian/dotfiles/blob/main/data/packages.json)
- The `forge` package repository configured before the first apply, because the
  first apply installs packages that exist only in forge
- A CPU that supports `x86-64-v3`, because `forge` packages compile for that
  level, which older generic `x86_64` CPUs do not support

`forge` is an Arch package repository (like `core` or `extra`) I made to make my
life easier. Run the following commands to set it up:

```sh
sudo pacman-key --add <(curl -fsSL https://athaurian.github.io/forge/signing_key.asc)
sudo pacman-key --lsign-key 6E299CB692113F71A3ABC006EAC1C444324DD6C6
echo -e '\n[forge]\nSigLevel = Required DatabaseOptional\nServer = https://athaurian.github.io/forge' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

## Install

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```

Run `make dark` or `make light` to generate the palette data and apply the
configuration for the first time. For what those targets do, see
[Palette system](palette-system.md). The first apply installs the machine's
missing packages from `data/packages.json`.
