---
template: home.html
---

# dotfiles

This is the documentation index. If you want an overview instead, see
[the project's README.md](https://github.com/athaurian/dotfiles/blob/main/README.md).
For the complete keybinding reference, see
[Keybindings](desktop/keybindings.md).

## Start here

1. Follow [Installation](installation.md) to prepare the host and deploy the
   configuration.
2. Read [Machines](machines.md) to identify the profile that applies to a given
   host.
3. Use the Desktop and System tables below to find the component whose behavior
   you need to understand.

The remaining pages can be read independently once these three are understood.

## Guides

| Guide                                 | Coverage                                                                        |
| :------------------------------------ | :------------------------------------------------------------------------------ |
| [Installation](installation.md)       | System requirements, the `forge` repository, and bootstrapping with `chezmoi`   |
| [Troubleshooting](troubleshooting.md) | Failed applies, stale files, palette state, and user units                      |
| [Glossary](glossary.md)               | Definitions of technical terms used across the guides, with external references |
| [Machines](machines.md)               | Display-server profiles for `thinkpad` and `optiplex`                           |
| [Neovim](neovim.md)                   | LazyVim, Catppuccin palette overrides, and Discord presence                     |
| [Development](development.md)         | Formatting, linting, and the `make check-*` targets used in CI                  |

## Desktop

| Guide                                                           | Coverage                                                                          |
| :-------------------------------------------------------------- | :-------------------------------------------------------------------------------- |
| [Keybindings](desktop/keybindings.md)                           | Shared shortcuts across Sway and i3, plus laptop-only bindings                    |
| [Shell](desktop/shell.md)                                       | Environment defaults, Vi readline mode, cache paths, and non-obvious aliases      |
| [Applications](desktop/applications.md)                         | Theme hooks, DND bypass rules, Fontconfig priorities, and app workarounds         |
| [Desktop entries](desktop/desktop-entries.md)                   | Local `.desktop` overrides for TUI tools, Qt6 theming, and Java tiling fixes      |
| [Pickers](desktop/pickers.md)                                   | Application launcher, power confirmation menus, and clipboard history             |
| [Status bar](desktop/statusbar.md)                              | Waybar and Polybar modules, polling fallbacks, and the 1366px width patch         |
| [Screenshots, lock, and idle](desktop/screenshots-lock-idle.md) | Capture shortcuts, lock screens, and idle inhibition                              |
| [Themes](desktop/theming.md)                                    | Live mode switching (`$mod+Shift+t`) and state persistence                        |
| [Wallpapers](desktop/wallpapers.md)                             | The `sw` rotator, [Hald CLUT](glossary.md#hald-clut) recoloring, and cache layout |

## System

| Guide                                      | Coverage                                                                                          |
| :----------------------------------------- | :------------------------------------------------------------------------------------------------ |
| [Palette system](system/palette-system.md) | Generation of application configs and wallpaper [LUTs](glossary.md#clut) from `meta/palette.toml` |
| [Background services](system/services.md)  | `systemd` user units, non-blocking session startup, and idle timers                               |
| [Battery charge limit](system/power.md)    | Kernel charge thresholds, skipped hosts, and manual removal                                       |
| [Calibre sync](system/calibre-sync.md)     | One-way staging and `rclone` sync from `~/Library` to Google Drive                                |
| [Utility scripts](system/tools.md)         | Helper scripts in `~/.local/bin`, including `prettier-math` and `wlsunset-location`               |
| [Git](system/git.md)                       | Signing, rebase defaults, and the destructive aliases                                             |
