# Theming

This page explains how colors work in this repository. It covers where the colors come from, how they get into your config files, how to switch between the dark and light variants, and how wallpapers are recolored to match. It is written for people who are new to this kind of setup, so every term is defined the first time it appears.

Everything inside this repo uses a custom theme called Flint (dark) and its light counterpart, Sand. Flint is a soft dark-grey theme built from colors in One Dark and Sway. They are applied to almost every app config in this repo.

## The color pipeline

The core idea is a single source of truth. One set of files defines every color, and everything else is derived from it. Nothing in this repo hardcodes a hex value twice. A hex value is a color written as six hexadecimal digits, like `#5a8bb0`.

The pipeline has three stages, and it helps to see them in order:

1. **Palette files.** The colors are defined in `palettes/flint/`, split into a shared file and one file per variant. This is where you edit a color by hand.
2. **The build script.** `scripts/build_palette_data.py` reads those files, validates every color, and exports the active variant into `.chezmoidata.yaml` in the effective chezmoi source root, which is `home/` in this repo.
3. **Templates.** The config files themselves are stored as `.tmpl` files. At apply time, chezmoi fills them in with the color data and writes the finished configs into your home directory.

So changing a color means editing one file and re-applying. The rest happens automatically.

For more details on the architecture, see [the palette system architecture](palette-system.md).

## The two variants

The theme has two variants, `dark` (Flint) and `light` (Sand).

Each variant carries exactly one accent, built into the semantic roles (`accent`, `accent_text`, `accent_bright`, `accent_strong`, `selection`, and `on_selection`). Both Flint and Sand use the same blue accent, one hue system at two lightness extremes. The warmth of Sand lives in its cream neutrals, not in its accent.

Window borders are the one deliberate exception. The `window_focused_border` role follows the theme's `text` color instead of the accent, light grey in Flint and dark in Sand. The `focus_border` role stays the neutral `overlay_strong` grey in both variants, so window borders stay neutral against any wallpaper.

A semantic role is a named job that a color does, like `background` or a focused window border. The actual color behind a role can change per variant, but the role name stays the same, which is why your configs can refer to roles instead of hex values.

## Switch variants

Export the variant you want, then apply with these commands:

```sh
make dark && chezmoi apply
make light && chezmoi apply
```

`make dark` runs the palette build script (`uv run --with pyyaml python3 scripts/build_palette_data.py --theme dark`), which validates the colors and exports the dark variant into `.chezmoidata.yaml`. The `make light` target does the same for Sand.

The generated `home/.chezmoidata.yaml` file is local-only and does not belong in version control. It is gitignored, because it changes every time you switch variants.

## Wallpaper theming

The repo also includes a helper called `flint-wallpaper` that uses [lutgen-rs](https://github.com/ozwaldorf/lutgen-rs) to recolor arbitrary wallpapers to match Flint or Sand. It caches both the generated LUTs and output images, so later runs reuse the cached results.

A lookup table (LUT) is a mapping that lutgen produces from your theme colors, used to shift every pixel of an image toward those colors. Generating a LUT is the expensive part, so the helper generates it once and reuses it until something about the theme changes.

LUT palette templates live in `home/dot_config/lutgen/` (`flint.tmpl`, `flint-cool.tmpl`, `flint-warm.tmpl`) and get rendered from the active theme data on apply.

```sh
# Recolor an image to match the active theme and set it as the wallpaper
flint-wallpaper --set ~/Pictures/Wallpapers/scenery.jpg

# Force a specific variant or palette
flint-wallpaper --theme light --palette warm --set ~/Pictures/Wallpapers/scenery.jpg

# Use Gaussian RBF instead of blur
flint-wallpaper --rbf --shape 96.0 --set ~/Pictures/Wallpapers/scenery.jpg
```

In these examples, `--theme light` forces the light variant, `--palette warm` picks the warm palette template, and `--rbf` switches from the default blur-based recoloring to a Gaussian radial basis function (RBF) method with the given shape value.

The helper is not bound to any keyboard shortcut. When a wallpaper path is set, the theme-apply hook runs it automatically after each variant switch, so the wallpaper matches the active variant without extra steps.

## Screenshots

Desktop screenshots (dark and light) live in `assets/` and are referenced from the README.

## Summary

Colors start in `palettes/flint/`, get validated and exported by the build script into `.chezmoidata.yaml`, and reach your apps through `.tmpl` templates at apply time. To switch variants, build the target variant, then apply with chezmoi. And when you want the wallpaper to match, `flint-wallpaper` recolors it with a cached LUT.
