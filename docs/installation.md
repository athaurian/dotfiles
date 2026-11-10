# Installation

My setup needs a few packages that the official Arch and CachyOS repositories
don't carry. Add my `forge` repository first, then apply the configuration with
`chezmoi`.

## Requirements

- Arch Linux with `bash` and systemd user services, CachyOS preferred
- A CPU that supports `x86-64-v3`, because `forge` builds packages for that
  microarchitecture level, which older generic `x86_64` CPUs do not support
- A hostname that selects the setup, covered in [Machines](machines.md). The
  files each setup skips are listed in
  [`.chezmoiignore`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoiignore),
  and the packages are listed in
  [`data/packages.json`](https://github.com/athaurian/dotfiles/blob/main/data/packages.json).

## Add the repository

I maintain `forge`, a package repository like `core` or `extra`. Some PKGBUILDs
carry local patches, and some packages aren't in the official repositories.

Add the repository and trust its signing key:

```sh
curl -fsSL https://athaurian.github.io/forge/signing_key.asc -o /tmp/forge-signing-key.asc
sudo pacman-key --add /tmp/forge-signing-key.asc
sudo pacman-key --lsign-key 6E299CB692113F71A3ABC006EAC1C444324DD6C6
echo -e '\n[forge]\nSigLevel = Required DatabaseOptional\nServer = https://athaurian.github.io/forge' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

## Apply the configuration

Once `forge` is ready, apply the configuration:

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```

The target generates the palette data and applies the configuration for the
first time. It also installs any missing packages. The
[clipboard picker](https://github.com/athaurian/clipboard-picker) and
[session manager](https://github.com/athaurian/session-manager) each install
with `uv` from their own repositories into `~/.local/bin`. For what the `dark`
and `light` targets do, see [Palette system](palette-system.md).
