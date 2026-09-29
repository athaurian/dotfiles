# Themes

One palette drives every surface on both machines. Dark mode and light mode
carry the same semantic roles, and each config switches with them.

## The color pipeline

One file defines every color, and everything else derives from it:

1. **The source.** [`meta/color-scheme.md`](../meta/color-scheme.md) holds the
   roles and values. Edit a color here.
2. **The generator.** `make palette` runs `meta/palette.py`, which validates the
   definitions and writes the derived data: `home/.chezmoidata.yaml` for the
   templates and the LUT palettes for wallpapers.
3. **The templates.** Configs that carry color live as `.tmpl` files. At apply
   time, chezmoi renders them with the palette data and writes the finished
   config into the home directory.

Changing a color is one edit, one `make palette`, and one `chezmoi apply`. For
the palette's rules and contrast checks, see
[Palette system](palette-system.md).

## Switch modes

```sh
make dark   # record dark mode, regenerate the palette data, apply
make light  # record light mode, regenerate the palette data, apply
```

The apply runs the mode hook, which updates the GTK theme and libadwaita through
dconf, re-renders the wallpaper for the new mode, and reloads the bar and tray
applets so they pick up the fresh icon theme and CSS.

`$mod+Shift+t` toggles from the keyboard through the `palette-mode` CLI, which
performs the same steps and reports through a notification.

## Wallpaper theming

`sw` recolors wallpapers to the active palette with the generated LUT and sets
them: sway runs `awww`, and optiplex runs feh. It records the wallpaper and mode
per machine, so `--restore` brings the right image back at login — sway does
that automatically, and `~/.fehbg` is written only by `sw`.

```sh
sw --set ~/Pictures/Wallpapers/scenery.jpg   # recolor and set
sw --next                                    # rotate through the pool
sw --restore                                 # re-apply the recorded wallpaper
```

`sw --help` lists the rest: palette choice, luminosity, blur versus RBF
sampling, and a forced LUT refresh. There is no wallpaper keybind; run it from a
terminal.
