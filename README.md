# Dotfiles

Hi. This is the setup I use daily. My desktop runs CachyOS, an Arch-based Linux
distribution, and [chezmoi](https://chezmoi.io) is the tool that manages it. The
configuration files live in a repository, and chezmoi installs them into your
home directory.

It's built around my color system. Instead of copying hex values into each
config file, the setup pulls every color from one palette, a single named set of
color definitions. The palette comes in two variants so the whole desktop can
switch between dark and light together. Flint is the dark variant, a neutral
grey theme, and Sand is the light variant with the same structure. Scripts and
services around the palette apply it to every app except Vesktop, which keeps
its own styling, and a session manager saves your open windows at logout and
restores them at login.

It's sort of wrong to call this repository `dotfiles`. The configuration files
are the dotfiles. By lines of code, they are the smaller half.

Look around and copy anything useful.

I wrote the sections in `docs/` for people who are new to this kind of setup.
They define terms as they appear, so if you already know your way around, skim
to what you need.

## Screenshots

The following table shows the dark and light desktop and launcher captures:

|          | Dark (Flint)                             | Light (Sand)                               |
| -------- | ---------------------------------------- | ------------------------------------------ |
| Desktop  | ![Dark desktop](assets/dark_stuff.png)   | ![Light desktop](assets/light_stuff.png)   |
| Launcher | ![Dark launcher](assets/dark_fuzzel.png) | ![Light launcher](assets/light_fuzzel.png) |

## Install the dotfiles

Start with the following commands, which initialize the repository, build the
dark palette, and apply the configs:

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
chezmoi apply
```

These steps assume you have already added my `forge` package repository and its
key. If you have not, see [the installation guide](docs/installation.md) for the
full walkthrough, including the `forge` setup and systemd services.

## Features

Use the following list to find the guide you need:

- [Theming](docs/theming.md). How every color gets from the palette into your
  config files, with dark and light variants and wallpaper recoloring to match.
- [Palette system](docs/palette-system.md). How the palette files, build script,
  validators, and templates fit together.
- [Session manager](docs/session-manager.md). How your Sway session is saved
  when you log out, power off, or reboot, and rebuilt at login.
- [Keybindings](docs/keybindings.md). How the shortcuts are connected, with the
  shortcut table and the movement and layout controls.
- [Pickers](docs/pickers.md). How the launcher, clipboard history, and
  notification history help you find things fast.
- [Screenshots, lock, and idle](docs/screenshots-lock-idle.md). How captures,
  the blurred lock screen, and the idle timer fit together.
- [Status bar](docs/statusbar.md). What the Waybar modules show, with music
  controls, update counts, and do not disturb.
- [Background services](docs/services.md). How the session target, power
  dialogs, drift check, ebook sync, and night light run without a window.
- [Installation](docs/installation.md). How to install the dotfiles on a fresh
  machine, with the package manifest and forge repository.

## Tips

- If a Qt6 app does not use the theme, install `qt6ct` and launch it with
  `QT_QPA_PLATFORMTHEME=qt6ct`.
- If Sway misbehaves, inspect the window tree with `swaymsg -t get_tree | jq .`.
  The `jq` command formats the JSON output.

## Notes

- `btop.conf` is managed entirely by chezmoi. Changes made inside the program
  itself do not persist unless you edit the file in the repo.
- This repository contains no secrets. If you ever add a file with credentials,
  encrypt that specific file with `chezmoi age encrypt` rather than encrypting
  the whole repository.
