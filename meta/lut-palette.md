# LUT palette: wallpaper recoloring

`lutgen` builds a color look-up table (LUT) from a palette and applies it to
wallpapers. It saves each table as an image called a Hald CLUT.

## The lutgen command

The following table lists each mechanism and its behavior:

| Mechanism         | Behavior                                                                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Custom palette    | Holds one hexadecimal color per line in `~/.config/lutgen/NAME`, where `NAME` is the palette name. Each color is written with or without `#` |
| Palette selection | `-p NAME` selects the named palette                                                                                                          |
| Gaussian blur     | The default interpolation. The `-r RADIUS` flag sets the blur radius, which is also the Gaussian sigma.                                      |
| Gaussian RBF      | Enable it with `-R`, and set the shape with `-s` and the neighbor count with `-n`                                                            |
| Shepard           | Enable it with `-S`, which interpolates by inverse distance                                                                                  |
| Nearest neighbor  | Enable it with `-N`, which disables interpolation and produces a posterized result                                                           |
| `-P`              | Preserves the source image's luminance after interpolation                                                                                   |
| `-L FACTOR`       | Adjusts weighting toward colorful or grayscale matches                                                                                       |
| `-l LEVEL`        | Sets the Hald CLUT resolution. `10` is the default working level, and `16` stores the complete sRGB space                                    |
| `lutgen apply`    | Applies a provided Hald CLUT, or generates one from the palette and applies it in one command                                                |
| `lutgen generate` | Writes a Hald CLUT to the current directory unless an output path is supplied                                                                |

## Palette contents

### Chromatic intermediates

`meta/palette.py` inserts intermediate colors between each pair of neighboring
neutrals when it builds a palette. For every chromatic color it also derives a
tint at each neutral lightness. The tint's chroma, a measure of color intensity,
shrinks with the lightness distance from the source color. The two derivation
parameters are `N_RAMP` and `K_CHROMA` in `meta/palette.py`.

## Application parameters

The `sw` utility builds look-up tables for wallpapers and passes flags to
`lutgen`. Its default values live in `sw` under `home/dot_local/bin/`.

## File layout

The following table lists each palette file and directory and its purpose:

| Path                                   | Purpose                       |
| -------------------------------------- | ----------------------------- |
| `home/dot_config/lutgen/neutral`       | Checked-in dark-mode palette  |
| `home/dot_config/lutgen/neutral-light` | Checked-in light-mode palette |
| `~/.cache/sw/luts/`                    | Runtime Hald CLUT cache       |
| `~/.cache/sw/wallpapers/`              | Recolored wallpaper output    |

## Validation

The following table lists each property to check in a recolored wallpaper and
what to look for:

| Property            | What to inspect                                                             |
| ------------------- | --------------------------------------------------------------------------- |
| Gradient continuity | Smooth source gradients should not collapse into a handful of visible bands |
| Hue separation      | Distinct source hues should not bleed into unrelated palette families       |
| Luminance           | Major light and dark structure should survive recoloring                    |
| Palette boundary    | Output colors should come from the generated palette                        |
| Detail              | Fine image structure should remain legible after recoloring                 |
