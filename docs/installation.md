# Installation

## Prerequisites

- Arch Linux with `bash` and systemd user services, CachyOS preferred
- A hostname of `thinkpad` or `optiplex`, because the hostname selects the
  entries that `.chezmoiignore` skips and the machine's package list in
  `data/packages.json`
- The `forge` package repository configured first, because its packages compile
  for `x86-64-v3`, which older generic `x86_64` CPUs do not support

The following commands complete the `forge` repository setup:

```sh
sudo pacman-key --add <(curl -fsSL https://athaurian.github.io/forge/signing_key.asc)
sudo pacman-key --lsign-key 45EAC3E28FC392FC4418F415C0C5B611BF77F6E5
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
