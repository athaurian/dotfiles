# Desktop entries

Local `.desktop` files in `home/dot_local/share/applications/` override system
entries in `/usr/share/applications/` to fix toolkit theming, tiling window
manager quirks, and terminal launching from `fuzzel` / `rofi`.

## Why each override exists

| Entry                                            | Reason for local override                                                                                                                                                                                |
| :----------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `btop.desktop`, `nvim.desktop`, `zellij.desktop` | Launches each TUI application inside `kitty`. `btop` also sets `--title=btop`, which the Sway and i3 title rules use to open it as a centered floating window.                                           |
| `org.keepassxc.KeePassXC.desktop`                | Prepends `env QT_QPA_PLATFORMTHEME=qt6ct` to `Exec=` so KeePassXC always respects the `qt6ct` palette even when launched by D-Bus activation or a desktop portal that did not inherit `~/.bash_profile`. |
| `logisim-evolution.desktop`                      | Sets `_JAVA_AWT_WM_NONREPARENTING=1` so Java Swing/AWT menus and dialogs render properly inside non-reparenting tiling window managers (Sway and i3) instead of opening as blank gray boxes.             |

## Default applications (`mimeapps.list`)

`home/dot_local/share/applications/mimeapps.list` routes web links to
`helium-browser`, directories to `thunar`, PDFs and EPUBs to `zathura`, images
to `imv`, and plain text / source files to `nvim`.
