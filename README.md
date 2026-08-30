# dotfiles

Hi. This repository sets up a CachyOS desktop with [chezmoi](https://chezmoi.io). It is built around a custom color system, Flint (dark) and Sand (light), plus the scripts and services that handle theming, session management, and everyday shortcuts.

Look around, and copy anything useful.

The sections in `docs/` are written for people who are new to this kind of setup. They define terms as they appear, so if you already know your way around, skim to what you need.

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

- **[Flint and Sand theming](docs/theming.md)**. How every color gets from a single source of truth into your config files, with dark and light variants, contrast validation, and per-app color generation through chezmoi templates. The architecture details are in [the palette system guide](docs/palette-system.md).
- **[Session manager](docs/session-manager.md)**. How your Sway session is saved when you log out, power off, or reboot, and rebuilt at login.
- **[Keybindings](docs/keybindings.md)**. How the shortcuts are connected, the shortcut reference table, and the movement and layout controls.

## Tips

- Press `Super+Shift+E` to log out. This stops `sway-session.target`, which cleans up session services.
- If a Qt6 app does not use the theme, install `qt6ct` and launch it with `QT_QPA_PLATFORMTHEME=qt6ct`.
- If a service misbehaves, check it with `journalctl --user -u SERVICE_NAME`, replacing `SERVICE_NAME` with the service name.
- If Sway misbehaves, inspect the window tree with `swaymsg -t get_tree | jq .` (the `jq` command formats the JSON output).

## Notes

- `btop.conf` is managed entirely by chezmoi. Changes made inside the program itself do not persist unless you edit the file in the repo.
- The lock script uses the `swaylock` binary. It comes from `swaylock-effects` when that package is installed, and from the plain `swaylock` package otherwise.
- `~/.local/bin/flint-wallpaper` is a standalone helper that themes wallpaper images with lutgen and caches LUTs and outputs. It is not bound to any shortcut, but the theme-apply hook runs it automatically when a wallpaper path is set. Run it with `--help` for usage.
- Books added to `~/Library` are synced to Google Drive automatically. Every 30 minutes, `calibre-sync.timer` stages all EPUBs and PDFs flat and mirrors them to `gdrive:Books` with rclone, so they are available on other devices. Check on it with `journalctl --user -u calibre-sync`.
- This repository contains no secrets. If you ever add a file with credentials, encrypt that specific file with `chezmoi age encrypt` rather than encrypting the whole repository.
