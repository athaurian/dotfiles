# Themes

Press `$mod+Shift+t` to switch between dark and light without restarting the
session. To change the palette colors, edit
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml)
and run `make dark` or `make light`. For more information about these targets,
see the [Palette system](palette-system.md) page.

I wrote a script named `sw` to handle recoloring based on the generated palette.
For more information, run `sw --help` or read the
[`executable_sw`](https://github.com/athaurian/dotfiles/blob/main/home/dot_local/bin/executable_sw)
script.

The file `~/.local/state/palette-mode` records the current mode. The only valid
values are `dark` and `light`. If the file is missing or unreadable, the mode is
`dark`. `make dark` and `make light` write this file and apply the
configuration. `make palette MODE=light` and `make palette MODE=dark` render the
palette data. These commands do not change the recorded mode.

## Live palette updates

Open Neovim windows repaint when the palette changes, so you do not have to
restart the editor after `make dark` or `make light`.
