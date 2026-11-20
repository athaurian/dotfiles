# LUT palette: wallpaper recoloring

A Hald CLUT is a color lookup table encoded as a square image: each pixel
position represents one color of the color space, and recoloring replaces a
source color with the value found at the corresponding position, interpolating
between entries. `lutgen` builds one from a palette, and `sw` applies it to
wallpapers. See the
[site glossary](https://athaurian.github.io/dotfiles/glossary/#hald-clut) for
the definition and its source.

## The lutgen command

The command exposes three groups of options: interpolation modes, result
options, and subcommands.

### Interpolation modes

| Mode             | Selecting flag | Parameter flags | Notes                                                   |
| :--------------- | :------------- | :-------------- | :------------------------------------------------------ |
| Gaussian blur    | Default        | `-r RADIUS`     | Radius is also the Gaussian sigma                       |
| Gaussian RBF     | `-R`           | `-s`, `-n`      | Shape and neighbor count                                |
| Shepard          | `-S`           | —               | Interpolates by inverse distance                        |
| Nearest neighbor | `-N`           | —               | Disables interpolation and produces a posterized result |

### Options

| Option         | Effect                                                                                              |
| :------------- | :-------------------------------------------------------------------------------------------------- |
| Custom palette | Holds one hexadecimal color per line in `~/.config/lutgen/NAME`; each color may include or omit `#` |
| `-p NAME`      | Selects the named palette                                                                           |
| `-P`           | Preserves the source image's luminance after interpolation                                          |
| `-L FACTOR`    | Adjusts weighting toward colorful or grayscale matches                                              |
| `-l LEVEL`     | Sets the Hald CLUT resolution; `10` is the working default and `16` stores the complete sRGB space  |

### Subcommands

| Command           | Effect                                                                         |
| :---------------- | :----------------------------------------------------------------------------- |
| `lutgen apply`    | Applies a provided Hald CLUT, or generates one from the palette and applies it |
| `lutgen generate` | Writes a Hald CLUT to the current directory unless an output path is supplied  |

## Palette contents

### Chromatic intermediates

The palette generator inserts intermediate colors between each pair of
neighboring neutrals. For every chromatic color it also derives a tint at each
neutral lightness. The tint's chroma, a measure of color intensity, shrinks with
the lightness distance from the source color. Two derivation parameters control
this step:

| Parameter  | Role                                                                |
| :--------- | :------------------------------------------------------------------ |
| `N_RAMP`   | Number of intermediate colors inserted between neighboring neutrals |
| `K_CHROMA` | Rate at which chroma falls with lightness distance                  |

For a chromatic color with chroma `Ch` at source lightness `Lh`, a tint at
neutral lightness `Lr` receives `Ch * max(0, 1 - abs(Lr - Lh) * K_CHROMA)`. The
factor is clamped at zero, which makes a distant tint neutral rather than
negative.

## Application parameters

The wallpaper utility builds lookup tables and passes flags to `lutgen`. Its
render defaults are constants in `home/dot_local/bin/executable_sw`. The
complete set of flags, environment variables, and defaults is listed in
[Wallpapers](../docs/desktop/wallpapers.md#options-and-environment-overrides).

## File layout

The table lists the locations involved in recoloring.

| Path                                   | Purpose                       |
| :------------------------------------- | :---------------------------- |
| `home/dot_config/lutgen/neutral`       | Checked-in dark-mode palette  |
| `home/dot_config/lutgen/neutral-light` | Checked-in light-mode palette |
| `$XDG_CACHE_HOME/sw/luts/`             | Runtime Hald CLUT cache       |
| `$XDG_CACHE_HOME/sw/wallpapers/`       | Recolored wallpaper output    |

## Validation

The table gives the criteria for inspecting a recolored wallpaper.

| Property            | Inspection criterion                                                        |
| :------------------ | :-------------------------------------------------------------------------- |
| Gradient continuity | Smooth source gradients should not collapse into a handful of visible bands |
| Hue separation      | Distinct source hues should not bleed into unrelated palette families       |
| Luminance           | Major light and dark structure should survive recoloring                    |
| Palette boundary    | Output colors should come from the generated palette                        |
| Detail              | Fine image structure should remain legible after recoloring                 |
