# Installation

## Prerequisites

- **Arch Linux or CachyOS** on an **`x86-64-v3`** CPU (Haswell / Zen 1 or
  newer). Packages in my custom repository are compiled with `-march=x86-64-v3`
  and will crash with `SIGILL` on older processors.
- **Hostname**: `chezmoi` templates select the X11/i3 desktop profile only when
  the system hostname is literally `optiplex`. Any other hostname receives the
  Wayland/Sway `thinkpad` profile.

## 1. Add the `forge` package repository

Several desktop components (`calpdf-git`, `polybar-pinned`,
`session-manager-git`, and `clipboard-picker-git`) come from my signed
[`forge`](https://github.com/athaurian/forge) repository.

Import and locally sign the repository key:

```bash
curl -fsSL https://athaurian.github.io/forge/signing_key.asc | sudo pacman-key --add -
sudo pacman-key --lsign-key 6E299CB692113F71A3ABC006EAC1C444324DD6C6
```

Append the repository to `/etc/pacman.conf`:

```ini
[forge]
SigLevel = Required DatabaseOptional
Server = https://athaurian.github.io/forge/$arch
```

Synchronize and upgrade your system packages:

```bash
sudo pacman -Syu
```

## 2. Bootstrap the dotfiles

Running `make dark` (or `make light`) inside the `chezmoi` checkout generates
the theme files from `meta/palette.toml`, installs required packages, and
applies the configuration to `$HOME`:

```bash
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```
