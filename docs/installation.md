# Installation

This page walks through installing the dotfiles on a fresh machine.

## Overview

The repository is a collection of dotfiles managed by
[chezmoi](https://chezmoi.io), which stores them in a source directory and
installs them into the home directory. The checkout root
(`~/.local/share/chezmoi`) holds the repo tooling — the Makefile, `meta/`, and
`data/` — while `.chezmoiroot` makes `home/` the source root that chezmoi
applies from. Some source files are `.tmpl` templates that chezmoi renders at
apply time with the palette data and machine-specific values.

## Assumptions

- Arch Linux (CachyOS preferred)
- `bash` as the interactive shell
- systemd user services
- The hostname is `thinkpad` or `optiplex`: it selects the per-machine file set
  (`.chezmoiignore`) and the machine's package list (`data/packages.json`).

thinkpad runs Sway on Wayland; optiplex runs i3 on X11. Everything else in this
repository adapts to both.

## The forge repository

> [!CAUTION] The packages served by the `forge` repository are compiled with
> `x86-64-v3` optimizations. They do not run on older generic `x86_64` CPUs.

Some packages are not in the official repositories. They come from `forge`, a
custom package repository hosted under the same GitHub account as these
dotfiles. The GTK theme, the fonts, and a few utilities come from there, so
configure it before the first apply. Add the repository and its signing key to
pacman:

```sh
sudo pacman-key --add <(curl -fsSL https://athaurian.github.io/forge/signing_key.asc)
sudo pacman-key --lsign-key 45EAC3E28FC392FC4418F415C0C5B611BF77F6E5
echo -e '\n[forge]\nSigLevel = Required DatabaseOptional\nServer = https://athaurian.github.io/forge' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

The first two commands import and locally sign the repository key, the third
appends the repository to pacman's configuration, and the last syncs the package
database. If `forge` is missing when the first apply runs, the onboarding script
prints these same commands and stops.

## Install the configuration

Three commands install the configs:

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```

`make dark` records the mode, builds the palette data, and applies the
configuration; use `make light` for the light mode. During the first apply the
onboarding script installs the machine's missing packages: it ensures `jq`,
computes the missing set from `data/packages.json` with `pacman -T`, installs it
with `paru` when that is present, and otherwise installs the repository packages
with `pacman` and prints the AUR packages to install by hand.

## Finish the setup

Two things are installed but not started by the apply:

- **The display manager.** The graphical session is started by `ly`, whose
  `/etc/ly/config.ini` is not managed by this repository. It logs the session to
  `~/.local/state/ly-session.log`.
- **The session units.** The session targets start at login through the
  `*-session.target.wants` symlink directories, which the apply installs.
  Logging into the desktop then starts the user services with the session; see
  [Background services](services.md).

## Package management

Package selections live in `data/packages.json`, split into `pacman` (grouped by
area), `cachyos`, `aur`, `custom` (the `forge` packages), and
`machines.<hostname>` for per-machine additions. Edit the manifest and re-run
`chezmoi apply`: the rendered onboarding script embeds the manifest's hash, so a
change re-runs it and installs only what is missing.
