# Themes

Press `$mod+Shift+t` to toggle between dark and light on the fly. But if you
ever need to change the actual colors, edit
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml)
and run `make dark` or `make light`. Read the
[Palette system](palette-system.md) section for more information about those
targets.

I wrote a script named `sw` to handle recoloring based on the generated palette.
The script provides these commands:

| Command          | Action                                           |
| ---------------- | ------------------------------------------------ |
| `sw --set IMAGE` | Set an image as the wallpaper                    |
| `sw --next`      | Rotate to the next wallpaper                     |
| `sw --prev`      | Return to the previously shown wallpaper         |
| `sw --restore`   | Re-apply the recorded wallpaper without rotating |

For more information, run `sw --help` (or, y'know, read the
[`executable_sw`](https://github.com/athaurian/dotfiles/blob/main/home/dot_local/bin/executable_sw)
script yourself).

## Hot-reloading

Neovim watches `lua/plugins/colorscheme.lua`, which the palette targets rewrite
with the new colors. The watcher ignores the other files from the same
`chezmoi apply` and coalesces the burst, so open editors repaint without a
restart.
