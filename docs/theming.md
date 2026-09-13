# Themes

Everything in this repository uses one theme: Flint in dark mode, Sand in light
mode. The two variants drive the desktop's appearance setting, and the app
configs in the repo switch at the same time, except Vesktop, which keeps its own
styling and inherits only fonts.

## The color pipeline

One set of files defines every color, and everything else derives from it.

1. **Palette files.** The colors are defined in `palettes/flint/`, split into a
   shared file and one file per variant. Edit a color here.
2. **The build script.** `scripts/build_palette_data.py` validates the
   definitions and writes the palette into `.chezmoidata.yaml` in the chezmoi
   source root, which is `home/` in this repo.
3. **Templates.** Config files are stored as `.tmpl` files. At apply time,
   chezmoi renders them with the palette data and everything else they
   reference, and writes the finished configs into the home directory.

Changing a color is one edit, one build, and one apply. For the file layout and
the derived formats, see [Palette system](palette-system.md).

## The two variants

A semantic role is a named job a color does, like `background` or a focused
window border. Each variant carries exactly one accent, expressed through the
semantic roles (`accent`, `accent_text`, `accent_bright`, `accent_strong`,
`selection`, and `on_selection`). Configs refer to roles instead of hex values,
so the same role can point at a different color in each variant.

Both variants share one hue system at two lightness extremes. The neutrals are
sterile cool grays with chroma reserved for meaningful states, so photos and
third-party apps blend with the UI. Window borders are the one deliberate
exception to the accent: `window_focused_border` follows the neutral gray in
Flint and the near-black `text` color in Sand, so frames stay neutral against
any wallpaper.

## Switch variants

Use the following commands to switch:

```sh
make dark && chezmoi apply
make light && chezmoi apply
```

`make dark` runs the palette build script, which validates the colors and writes
`.chezmoidata.yaml` with the dark variant active. `make light` does the same for
Sand. The generated `home/.chezmoidata.yaml` file is local-only and excluded by
Git, because it changes on every switch.

## Wallpaper theming

The `flint-wallpaper` helper uses
[lutgen-rs](https://github.com/ozwaldorf/lutgen-rs) to recolor arbitrary
wallpapers to match the active theme. It caches both the generated lookup table
(LUT) and the output images, so later runs reuse cached results. Generating a
LUT is the expensive part, so the helper generates it once and reuses it until
the theme, palette, or flags change.

LUT palette templates live in `home/dot_config/lutgen/`. The `flint.tmpl`,
`flint-cool.tmpl`, and `flint-warm.tmpl` files render from the active theme data
on apply. Each file is one LUT palette: `flint` balances every hue, `flint-cool`
keeps only the cool hues, and `flint-warm` keeps only the warm ones.

The following commands show common uses:

```sh
# Recolor an image to match the active theme and set it as the wallpaper
flint-wallpaper --set ~/Pictures/Wallpapers/scenery.jpg

# Force a specific variant or palette
flint-wallpaper --theme light --palette warm --set ~/Pictures/Wallpapers/scenery.jpg

# Use Gaussian RBF instead of blur
flint-wallpaper --rbf --shape 96.0 --set ~/Pictures/Wallpapers/scenery.jpg
```

The helper is not bound to a keyboard shortcut. The rotate script bound to
`Super+Shift+w` and `Super+Control+w` picks the next or previous wallpaper from
its queue and recolors it with the helper. When a wallpaper path is set, the
chezmoi hook that applies the theme runs it after each variant switch,
preferring the last wallpaper used in the theme's rotation, so the wallpaper
matches the active variant without extra steps. Run `flint-wallpaper --help` for
usage.
