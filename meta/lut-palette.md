# LUT palette: wallpaper recoloring

`lutgen` builds a color look-up table (LUT) from a palette and applies it to
wallpapers. It saves each table as an image called a Hald CLUT.

## The lutgen command

| Mechanism         | Behavior                                                                                                  |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| Custom palette    | Holds one hexadecimal color per line in `~/.config/lutgen/<name>`, with or without `#`                    |
| Palette selection | `-p <name>` selects the named palette                                                                     |
| Gaussian blur     | The default interpolation. The `-r RADIUS` flag sets the blur radius, which is also the Gaussian sigma.   |
| Gaussian RBF      | Enable it with `-R`, and set the shape with `-s` and the neighbor count with `-n`                         |
| Shepard           | Enable it with `-S`, which interpolates by inverse distance                                               |
| Nearest neighbor  | Enable it with `-N`, which disables interpolation and produces a posterized result                        |
| `-P`              | Preserves the source image's luminance after interpolation                                                |
| `-L FACTOR`       | Adjusts weighting toward colorful or grayscale matches                                                    |
| `-l LEVEL`        | Sets the Hald CLUT resolution. `10` is the default working level, and `16` stores the complete sRGB space |
| `lutgen apply`    | Applies a provided Hald CLUT, or generates one from the palette and applies it in one command             |
| `lutgen generate` | Writes a Hald CLUT to the current directory unless an output path is supplied                             |

## Palette contents

### Chromatic intermediates

`meta/palette.py` inserts `N` intermediate colors between each pair of
neighboring neutrals when it builds a palette. For every chromatic color it also
derives a tint at each neutral lightness. The tint's chroma, a measure of color
intensity, shrinks in proportion to `k` and the lightness distance from the
source color.

| Parameter | Value |
| --------- | ----: |
| `N`       |   `2` |
| `k`       | `0.5` |

## Application parameters

By default, the `sw` utility passes these flags when it builds a look-up table
for a wallpaper.

| Flag | Value  | Purpose                                                                            |
| ---- | ------ | ---------------------------------------------------------------------------------- |
| `-R` |        | Enables Gaussian RBF interpolation                                                 |
| `-s` | `96`   | Sets the RBF shape, which limits excessive bleeding between distant hues           |
| `-n` | `16`   | Sets how many of the nearest palette colors to consider                            |
| `-l` | `10`   | Sets the Hald CLUT level for the working pipeline                                  |
| `-P` |        | Preserves source luminance and retains image detail                                |
| `-L` | `1.05` | Slightly favors colorful matches while retaining the luminance-preserving behavior |

## File layout

| Path                                   | Purpose                       |
| -------------------------------------- | ----------------------------- |
| `home/dot_config/lutgen/neutral`       | Checked-in dark-mode palette  |
| `home/dot_config/lutgen/neutral-light` | Checked-in light-mode palette |
| `~/.cache/sw/luts/`                    | Runtime Hald CLUT cache       |
| `~/.cache/sw/wallpapers/`              | Recolored wallpaper output    |

## Validation

| Property            | What to inspect                                                             |
| ------------------- | --------------------------------------------------------------------------- |
| Gradient continuity | Smooth source gradients should not collapse into a handful of visible bands |
| Hue separation      | Distinct source hues should not bleed into unrelated palette families       |
| Luminance           | Major light and dark structure should survive recoloring                    |
| Palette boundary    | Output colors should come from the generated palette                        |
| Detail              | Fine image structure should remain legible after recoloring                 |
