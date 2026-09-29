# Keybindings

Shortcuts live in the two configs — `home/dot_config/sway/config.tmpl` for
thinkpad and `home/dot_config/i3/config.tmpl` for optiplex — and mostly use the
Super key (`$mod Mod4`). The distinctive, script-backed shortcuts are indexed in
[FEATURES.md](../FEATURES.md), and the full lists live in the configs. This page
covers the tiling controls both machines share and the wiring behind the
application shortcuts.

## Windows, workspaces, and layouts

Both configs give the same controls, with vim keys and the arrow keys
interchangeable:

| Binding                                     | Action                            |
| ------------------------------------------- | --------------------------------- |
| `$mod+h/j/k/l` or `$mod+arrows`             | Focus a window                    |
| `$mod+Shift+h/j/k/l` or `$mod+Shift+arrows` | Move a window                     |
| `$mod+1` … `$mod+0`                         | Switch to workspace 1–10          |
| `$mod+Shift+1` … `$mod+Shift+0`             | Move a window to workspace 1–10   |
| `$mod+a` / `$mod+Shift+a`                   | Focus parent / child container    |
| `$mod+v` / `$mod+o`                         | Split vertically / horizontally   |
| `$mod+w` / `$mod+s`                         | Tabbed / stacking layout          |
| `$mod+p`                                    | Toggle the split direction        |
| `$mod+f`                                    | Fullscreen                        |
| `$mod+q`                                    | Close the window                  |
| `$mod+r` then `h/j/k/l` or arrows           | Resize mode; `Return`/`Esc` exits |

## Scratchpads

- `$mod+grave` shows the drop terminal: a centered floating `foot` that hides
  again when you press it a second time.
- `$mod+minus` cycles hidden scratchpad windows; `$mod+Shift+minus` sends the
  focused window there.
- `$mod+Shift+space` toggles floating and, for a window that came from the
  scratchpad, returns it there; `$mod+space` moves focus between the tiled and
  the floating layer.

## Applications and wrappers

The configs bind shortcuts to names, and the names carry the fallbacks:

- `$mod+Return` runs the terminal, `$mod+b` the browser, and `$mod+e` the file
  manager.
- The browser runs through `wrapper_browser.sh`: it honors `$BROWSER` when set,
  otherwise tries `helium-browser`, `firefox`, `chromium`, and `google-chrome`
  in order.
- The file manager reads `$FILE_MANAGER` and falls back to `thunar`.
- The password manager (`$mod+Shift+p`) reads `$PASSWORD_MANAGER`, falls back to
  `keepassxc`, and launches it with the `qt5ct` theme because KeePassXC is still
  Qt5.

File associations (documents to the browser, PDFs to the reader, links to the
terminal where applicable) live in
`home/dot_local/share/applications/mimeapps.list.tmpl`.

## Reload

`$mod+Shift+c` reloads sway's configuration on thinkpad. On optiplex it reloads
i3 and restarts Polybar together.

Screenshots, locking, and the idle timer have their own shortcuts; see
[Screenshots, lock, and idle](screenshots-lock-idle.md).
