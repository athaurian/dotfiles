# Installation

## Prerequisites

- Arch Linux with `bash` and systemd user services, CachyOS preferred
- A hostname that decides the setup, covered in [Machines](machines.md). The
  files each setup skips live in
  [`.chezmoiignore`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoiignore),
  and the packages live in
  [`data/packages.json`](https://github.com/athaurian/dotfiles/blob/main/data/packages.json).
- The `forge` package repository, set up before the first apply
- A CPU that supports `x86-64-v3`, because `forge` packages compile for that
  level, which older generic `x86_64` CPUs do not support

`forge` is an Arch package repository (like `core` or `extra`) I made to make my
life easier. It contains some modified PKGBUILDs and packages that do not exist
at all in the official Arch/CachyOS repositories.

Run the following commands to set it up:

```sh
curl -fsSL https://athaurian.github.io/forge/signing_key.asc -o /tmp/forge-signing-key.asc
sudo pacman-key --add /tmp/forge-signing-key.asc
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
configuration for the first time. That first run also installs whatever packages
the machine is missing. For what those targets do, see
[Palette system](palette-system.md).
