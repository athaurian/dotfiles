# dotfiles

Hi. This is the setup I use daily. My desktop runs CachyOS, an Arch-based Linux distribution, and [chezmoi](https://chezmoi.io) is the tool that manages it. The configuration files live in a repository, and chezmoi installs them into your home directory.

It's built around my color system. Instead of copying hex values into each config file, the setup pulls every color from one palette, a single named set of color definitions. The palette comes in two variants so the whole desktop can switch between dark and light together. Flint is the dark variant, a warm dark grey theme, and Sand is the light variant with the same structure. Scripts and services around the palette apply it to every app, and a session manager saves your open windows at logout and restores them at login.

It's sort of wrong to call this repository `dotfiles`. The name fits the configuration files, and the repository also carries the programs that come with them, with tests and documentation of their own.

Look around and copy anything useful.

I wrote the sections in `docs/` for people who are new to this kind of setup. They define terms as they appear, so if you already know your way around, skim to what you need.

## Screenshots

Desktop screenshots live in [`assets/`](https://github.com/athaurian/dotfiles/tree/main/assets).

## Quick start

Start with the following commands, which initialize the repository, build the dark palette, and apply the configs:

```sh
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
chezmoi apply
```

These steps assume you have already added my `forge` package repository and its key. If you have not, see [the installation guide](docs/installation.md) for the full walkthrough, including the `forge` setup and systemd services.

## Highlights

- **[Flint and Sand theming](docs/theming.md)**. How every color gets from the palette into your config files, with dark and light variants, contrast validation, and per-app color generation through chezmoi templates. The architecture details are in [the palette system guide](docs/palette-system.md).
- **[Session manager](docs/session-manager.md)**. How your Sway session is saved when you log out, power off, or reboot, and rebuilt at login.
- **[Keybindings](docs/keybindings.md)**. How the shortcuts are connected, the shortcut reference table, and the movement and layout controls.

## Tips

- Press `Super+Shift+E` to log out. This stops `sway-session.target`, the unit that groups the session services, so they start and stop together.
- If a Qt6 app does not use the theme, install `qt6ct` and launch it with `QT_QPA_PLATFORMTHEME=qt6ct`.
- If a service misbehaves, check it with `journalctl --user -u SERVICE_NAME`, replacing `SERVICE_NAME` with the service name.
- If Sway misbehaves, inspect the window tree with `swaymsg -t get_tree | jq .` (the `jq` command formats the JSON output).

## Notes

- `btop.conf` is managed entirely by chezmoi. Changes made inside the program itself do not persist unless you edit the file in the repo.
- The lock script uses the `swaylock` binary. It comes from `swaylock-effects` when that package is installed, and from the plain `swaylock` package otherwise.
- `~/.local/bin/flint-wallpaper` is a standalone helper that themes wallpaper images with lutgen and caches LUTs and outputs. It is not bound to any shortcut. The script that applies a theme runs it whenever a wallpaper path is set, so the wallpaper follows the active variant. Run it with `--help` for usage.
- `calibre-sync.timer` mirrors every EPUB and PDF in `~/Library` to `gdrive:Books` with rclone every 30 minutes, staging the files flat and naming them from calibre's metadata. It needs an rclone remote named `gdrive` signed in to your Google Drive, which this repository does not set up. Without books, or without that remote, the timer fails and the journal says why. If you do not keep an ebook library, remove `symlink_calibre-sync.timer.tmpl` from `sway-session.target.wants/` before applying. Check on it with `journalctl --user -u calibre-sync`.
- This repository contains no secrets. If you ever add a file with credentials, encrypt that specific file with `chezmoi age encrypt` rather than encrypting the whole repository.
