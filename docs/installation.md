# Installation

## Prerequisites

- Arch Linux with `bash` and systemd user services, CachyOS preferred
- A hostname that selects the setup, covered in [Machines](machines.md). The
  files each setup skips are listed in
  [`.chezmoiignore`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoiignore),
  and the packages are listed in
  [`data/packages.json`](https://github.com/athaurian/dotfiles/blob/main/data/packages.json).
- The `forge` package repository, set up before the first apply
- A CPU that supports `x86-64-v3`, because `forge` builds packages for that
  microarchitecture level, which older generic `x86_64` CPUs do not support

`forge` is an Arch package repository, like `core` or `extra`, that I maintain.
It contains modified PKGBUILDs and packages that are not available in the
official Arch or CachyOS repositories.

Some packages apply a small patch to upstream code instead of forking it.
`swayfx-git` is one of them: Dunst shrinks a notification stack by resizing its
buffer, and an unpatched SwayFX keeps the layer shadow at the previous size. The
patched build makes the shadow follow the cards.

Run the following commands to add the repository and trust its signing key:

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
configuration for the first time. On first run, any missing packages are
installed automatically. The
[clipboard picker](https://github.com/athaurian/clipboard-picker) and
[session manager](https://github.com/athaurian/session-manager) are each
installed with `uv` from their own repositories, placing both tools in
`~/.local/bin`. For what those targets do, see
[Palette system](palette-system.md).
