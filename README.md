# Dotfiles

This is the setup I use daily on two machines: **thinkpad** (Sway on Wayland)
and **optiplex** (i3 on X11). Both run an Arch-based distribution and both are
managed by [chezmoi](https://chezmoi.io). Configuration files live in this
repository; chezmoi installs them into the home directory, and `.chezmoiignore`
plus `data/packages.json` split what each machine gets.

The repository is large by dotfile standards, and the config files are the
smaller half of it by lines. The other half is the tooling that builds and
checks what goes into them, plus the scripts and services that run the desktop
day to day.

Every part has its own guide under `docs/`, indexed below. `FEATURES.md` is the
full inventory of what this repository configures, and `AGENTS.md` holds the
operating rules for working on it.

Look around and take anything useful.

## Install

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```

`make dark` builds the palette and applies the configs; `make light` does the
same for the light mode. The `forge` package repository must be configured
first, and the first apply installs the machine's packages. See
[the installation guide](docs/installation.md) for the full walkthrough.

## Guides

- [Installation](docs/installation.md). Fresh-machine setup, the `forge`
  repository, and the package manifest.
- [Keybindings](docs/keybindings.md). The shortcut landscape and the wiring
  behind it.
- [Themes](docs/theming.md). How colors get from the palette into every config,
  and how wallpapers follow the active mode.
- [Palette system](docs/palette-system.md). Where the colors are defined and
  what derives from them.
- [Screenshots, lock, and idle](docs/screenshots-lock-idle.md). Captures, the
  lock screen, and the idle timer on both machines.
- [Status bar](docs/statusbar.md). What Waybar and Polybar show and do.
- [Background services](docs/services.md). The session groups, timers, and
  helpers that run without a window.
- [Pickers](docs/pickers.md). The launcher and the confirmation menus.

The feature-level index — keybinds, services, bar modules, tooling — is
[FEATURES.md](FEATURES.md). The palette's single source of truth is
[meta/color-scheme.md](meta/color-scheme.md).

## Notes

- Configs live here, not in the home directory: edits made inside a program are
  reverted by the next `chezmoi apply`, so edit the source instead.
- Qt6 applications run through `qt6ct`; KeePassXC is still Qt5, so its launchers
  pin it to `qt5ct`.
- The repository contains no secrets. If a file ever gains credentials, encrypt
  that file with `chezmoi age encrypt` rather than the whole repository.
