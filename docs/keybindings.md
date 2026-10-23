# Keybindings

`$mod` is the Super key, which is usually the key with the Windows logo. Every
binding here works on both machines. You can see the actual lists in
[`home/dot_config/sway/config.tmpl`](https://github.com/athaurian/dotfiles/blob/main/home/dot_config/sway/config.tmpl)
and
[`home/dot_config/i3/config.tmpl`](https://github.com/athaurian/dotfiles/blob/main/home/dot_config/i3/config.tmpl).
For the components that differ between the machines, see
[Machines](machines.md).

| Binding                                     | Action                                    |
| ------------------------------------------- | ----------------------------------------- |
| `$mod+h/j/k/l` or `$mod+arrows`             | Focus a window                            |
| `$mod+Shift+h/j/k/l` or `$mod+Shift+arrows` | Move a window                             |
| `$mod+1` through `$mod+0`                   | Switch to workspace 1-10                  |
| `$mod+Shift+1` through `$mod+Shift+0`       | Move a window to workspace 1-10           |
| `$mod+a` or `$mod+Shift+a`                  | Focus the parent or child container       |
| `$mod+v` or `$mod+o`                        | Split vertically or horizontally          |
| `$mod+w` or `$mod+s`                        | Set the tabbed or stacking layout         |
| `$mod+p`                                    | Toggle the split direction                |
| `$mod+f`                                    | Fullscreen                                |
| `$mod+q`                                    | Close the window                          |
| `$mod+r` then `h/j/k/l` or arrows           | Enter resize mode                         |
| `$mod+grave`                                | Open or hide the drop-down terminal       |
| `$mod+minus`                                | Cycle other scratchpad windows            |
| `$mod+Shift+minus`                          | Send the focused window to the scratchpad |
| `$mod+Shift+p`                              | Open or hide the password manager         |

Press `Return` or `Esc` to leave resize mode.

The drop-down terminal, clipboard picker, and password manager live in the
scratchpad and toggle with their own bindings. Send other windows there with
`$mod+Shift+minus` and cycle them with `$mod+minus`.

On `thinkpad`, I open the clipboard picker with `$mod+Ctrl+v`. See
[Pickers](pickers.md) for how it filters and previews entries.
