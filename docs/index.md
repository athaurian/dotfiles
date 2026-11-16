---
template: home.html
---

# dotfiles

This is the documentation index. If you want an overview instead, see
[the project's README.md](https://github.com/athaurian/dotfiles/blob/main/README.md).

## Guides

| Guide                           | Coverage                                                                      |
| :------------------------------ | :---------------------------------------------------------------------------- |
| [Installation](installation.md) | System requirements, the `forge` repository, and bootstrapping with `chezmoi` |
| [Machines](machines.md)         | Why `thinkpad` uses Wayland/Sway while `optiplex` stays on X11/i3             |
| [Neovim](neovim.md)             | LazyVim, Catppuccin palette overrides, and Discord presence                   |

## Desktop

| Guide                                                           | Coverage                                                                     |
| :-------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| [Keybindings](desktop/keybindings.md)                           | Shared shortcuts across Sway and i3, plus laptop-only bindings               |
| [Shell](desktop/shell.md)                                       | Environment defaults, Vi readline mode, cache paths, and non-obvious aliases |
| [Applications](desktop/applications.md)                         | Theme hooks, DND bypass rules, Fontconfig priorities, and app workarounds    |
| [Desktop entries](desktop/desktop-entries.md)                   | Local `.desktop` overrides for TUI tools, Qt6 theming, and Java tiling fixes |
| [Pickers](desktop/pickers.md)                                   | Application launcher, power confirmation menus, and clipboard history        |
| [Status bar](desktop/statusbar.md)                              | Waybar and Polybar modules, polling fallbacks, and the 1366px width patch    |
| [Screenshots, lock, and idle](desktop/screenshots-lock-idle.md) | Capture shortcuts, lock screens, and idle inhibition                         |
| [Themes](desktop/theming.md)                                    | Live mode switching (`$mod+Shift+t`) and state persistence                   |
| [Wallpapers](desktop/wallpapers.md)                             | The `sw` rotator, Hald CLUT recoloring, and cache layout                     |

## System

| Guide                                      | Coverage                                                                            |
| :----------------------------------------- | :---------------------------------------------------------------------------------- |
| [Palette system](system/palette-system.md) | How `meta/palette.toml` generates app configs and wallpaper LUTs                    |
| [Background services](system/services.md)  | `systemd` user units, non-blocking session startup, and idle timers                 |
| [Calibre sync](system/calibre-sync.md)     | One-way staging and `rclone` sync from `~/Library` to Google Drive                  |
| [Utility scripts](system/tools.md)         | Helper scripts in `~/.local/bin`, including `prettier-math` and `wlsunset-location` |
