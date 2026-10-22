# Themes

Trigger the `$mod+Shift+t` keybind to toggle between dark and light on-the-fly.
But if you ever need to change the actual colors, edit
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml)
and run `make dark` or `make light`. Read the
[Palette system](palette-system.md) section for more information about those
targets.

I wrote a script named `sw` to handle recoloring based on the generated palette.
Run `sw --set IMAGE` to set an image as the desktop background and `sw --next`
to rotate to the next one. To go back to the previously shown wallpaper, run
`sw --prev`. Run `sw --restore` to re-apply the recorded wallpaper without
rotating it.

For more information, run `sw --help` (or, y'know, read the
[`executable_sw`](https://github.com/athaurian/dotfiles/blob/main/home/dot_local/bin/executable_sw)
script yourself).

## Hot-reloading

Neovim reloads its colorscheme when the palette changes. Open editors repaint
without a restart.
