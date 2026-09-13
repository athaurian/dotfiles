# Dotfiles

This is the setup I use daily. The desktop runs CachyOS, an Arch-based Linux
distribution, and [chezmoi](https://chezmoi.io) manages it. Configuration files
live in this repository, and chezmoi installs them into the home directory.

The repository is large by dotfile standards, and the config files are the
smaller half of it by lines of code. The other half is the tooling that builds
and checks what goes into them, plus the scripts and services that run the
desktop day to day.

Every part has its own guide under `docs/`, and the Features section below is
the index.

Look around and take anything useful.

## Screenshots

The following table shows the desktop and launcher captures in both themes:

|          | Dark (Flint)                             | Light (Sand)                               |
| -------- | ---------------------------------------- | ------------------------------------------ |
| Desktop  | ![Dark desktop](assets/dark_stuff.png)   | ![Light desktop](assets/light_stuff.png)   |
| Launcher | ![Dark launcher](assets/dark_fuzzel.png) | ![Light launcher](assets/light_fuzzel.png) |

## Install

The following commands initialize the repository, build the dark palette, and
apply the configs:

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
chezmoi apply
```

These steps assume the `forge` package repository and its key are already
configured. See [the installation guide](docs/installation.md) for the full
walkthrough, including the `forge` setup and the systemd services.

## Features

Use the following list to find the guide for each part:

- [Themes](docs/theming.md). How colors get from the palette into each config
  file, and how wallpapers are recolored to match.
- [Palette system](docs/palette-system.md). The palette files, the build script,
  and the contrast checks.
- [Session manager](docs/session-manager.md). How the Sway session is saved at
  logout and restored at login.
- [Keybindings](docs/keybindings.md). The shortcut table and the wiring behind
  it.
- [Pickers](docs/pickers.md). The launcher, clipboard history, and notification
  history.
- [Screenshots, lock, and idle](docs/screenshots-lock-idle.md). Captures, the
  lock screen, and the idle timer.
- [Status bar](docs/statusbar.md). What the Waybar modules show.
- [Background services](docs/services.md). The session group, drift check, ebook
  sync, and night light.
- [Installation](docs/installation.md). A fresh-machine install, with the
  package manifest and the forge repository.

## Tips

- Qt applications use the Fusion style, configured through `qt6ct`
  (`QT_QPA_PLATFORMTHEME=qt6ct`). KeePassXC is still Qt5, so its launcher pins
  it to `qt5ct`.
- To inspect the Sway window tree, run `swaymsg -t get_tree | jq .`.

## Notes

- `btop.conf` is managed by chezmoi. Changes made inside the program are
  overwritten the next time chezmoi applies, so edit the file in the repository
  instead.
- The repository contains no secrets. If a file ever gains credentials, encrypt
  that file with `chezmoi age encrypt` rather than the whole repository.
