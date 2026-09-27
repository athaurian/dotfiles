# LUT palette: wallpaper recoloring

The LUT palette maps wallpapers into the locked desktop palette defined by
`meta/color-scheme.md`. The palette is generated, checked in, and consumed by
`lutgen`; it is not hand-tuned per wallpaper.

## Design

- **Use the locked palette as the source.** The neutral ramp, seven chromatic
  base colors, and seven bright colors come only from `meta/color-scheme.md`.
- **Add mathematical intermediates.** The locked colors alone are too sparse for
  photographic gradients. Intermediate colors are generated in OKLCH so that
  lightness and chroma change continuously rather than snapping to a small set
  of stops.
- **Keep the artifact reproducible.** The generator defines the formula; the
  checked-in palette file contains the generated hexadecimal values.

## lutgen behavior

The locally verified lutgen version is `1.1.1`.

| Mechanism         | Behavior                                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| Custom palette    | One hexadecimal color per line in `~/.config/lutgen/<name>`, with or without `#`                        |
| Palette selection | `-p <name>` selects the named palette                                                                   |
| Gaussian blur     | Default interpolation; `-r RADIUS` controls the sigma/radius parameter                                  |
| Gaussian RBF      | `-R`, with shape controlled by `-s` and neighbor count by `-n`                                          |
| Shepard           | Alternative interpolation method                                                                        |
| Nearest neighbor  | `-N`; produces posterized results                                                                       |
| `-P`              | Preserves the source image's luminance after interpolation                                              |
| `-L FACTOR`       | Adjusts weighting toward colorful or grayscale matches                                                  |
| `-l LEVEL`        | Sets Hald CLUT resolution; `10` is the default working level, while `16` stores the complete sRGB space |
| `lutgen apply`    | Generates and applies the LUT in one command                                                            |
| `lutgen generate` | Writes a Hald CLUT to the current directory unless an output path is supplied                           |

Always give `lutgen generate` an explicit output path when it is used directly.
There is no built-in repository LUT cache directory; cache management is part of
our own workflow.

## Palette contents

The locked input contains 25 colors:

- **Neutrals.** The eleven-step ramp from `#101010` through `#FFFFFF`.
- **Chromatics.** Seven base hues and their seven bright variants.

The generated palette adds intermediate colors to reduce posterization while
remaining derived from those locked values.

### Neutral intermediates

For adjacent locked ramp values `A` and `B`, emit `N` evenly spaced OKLCH
interpolants:

```text
A + i/(N+1) × (B - A),  i = 1..N
```

Interpolation applies independently to OKLCH `L`, `C`, and `H`. The resulting
colors fill the gaps between the locked neutral lightness steps.

### Chromatic intermediates

For each hue, use its OKLCH base chroma `C` and hue angle `H`. At each neutral
ramp lightness `L_ramp`, derive:

```text
oklch(L_ramp, C × (1 - |L_ramp - L_hue| × k), H)
```

`N` controls how many intermediate colors are generated. `k` controls how fast
chroma falls toward the black and white extremes. The starting values are:

| Parameter | Value |
| --------- | ----: |
| `N`       |   `2` |
| `k`       | `0.5` |

Adjust these only when the generated palette demonstrates a concrete rendering
problem.

## Generated artifact

The generated palette is stored at:

```text
home/dot_config/lutgen/neutral
```

Generation order is:

1. Locked colors from `meta/color-scheme.md`.
2. Generated neutral intermediates.
3. Generated chromatic intermediates.
4. Lightness-sorted output as static hexadecimal values.

The file is checked in and reproducible. Do not hand-edit it.

The generator is intentionally a small Python script rather than a general
palette-building system. Do not introduce chezmoi templates, YAML, contrast
gates, or another palette abstraction for this workflow.

## Application parameters

The current working command is:

```sh
lutgen apply -p neutral -R -s 96 -n 16 -l 10 -P -L 1.05 img.png -o out.png
```

| Flag | Value  | Purpose                                                                           |
| ---- | ------ | --------------------------------------------------------------------------------- |
| `-R` |        | Gaussian RBF interpolation                                                        |
| `-s` | `96`   | RBF shape; limits excessive bleeding between distant hues                         |
| `-n` | `16`   | Use the 16 nearest palette colors                                                 |
| `-l` | `10`   | Hald CLUT level used for the working pipeline                                     |
| `-P` |        | Preserve source luminance and retain image detail                                 |
| `-L` | `1.05` | Slightly favor colorful matches while retaining the luminance-preserving behavior |

Treat these values, tested against real wallpapers, as one working parameter
set, not as universal lutgen defaults.

When tuning, change one parameter at a time. RBF shape and luminance weighting
are the first parameters to investigate when the neutral palette produces
undesired blending or loss of detail.

## File layout

| Path                             | Purpose                      |
| -------------------------------- | ---------------------------- |
| `home/dot_config/lutgen/neutral` | Checked-in generated palette |
| `~/.cache/lutgen/`               | Runtime LUT output/cache     |
| `~/Pictures/Wallpapers/neutral/` | Recolored wallpaper output   |

Always pass `-o` for generated output instead of relying on the current working
directory. Wallpaper selection is handled by the desktop wallpaper workflow.

## Workflow

1. **Change the source.** Edit a locked color or derivation specification in
   `meta/color-scheme.md`.
2. **Regenerate.** Run the palette generator so `home/dot_config/lutgen/neutral`
   reflects the new source values.
3. **Apply.** Recolor a wallpaper with the working lutgen parameters.
4. **Inspect.** Check the resulting image visually for gradients, hue bleeding,
   and preserved detail.
5. **Tune deliberately.** When the result is wrong, change one lutgen parameter,
   regenerate, and compare against the previous result.

Example:

```sh
lutgen apply -p neutral -R -s 96 -n 16 -l 10 -P -L 1.05 \
  ~/Pictures/Wallpapers/dark/flower-basket.jpg \
  -o ~/.cache/lutgen/neutral.png
```

Then display the output with the repository's wallpaper tooling.

## Validation

The palette itself should be reproducible from the documented inputs. Recoloring
also requires visual inspection because a mathematically valid LUT can still
produce an undesirable image.

Check at least these properties:

| Property            | What to inspect                                                             |
| ------------------- | --------------------------------------------------------------------------- |
| Gradient continuity | Smooth source gradients should not collapse into a handful of visible bands |
| Hue separation      | Distinct source hues should not bleed into unrelated palette families       |
| Luminance           | Major light and dark structure should survive recoloring                    |
| Palette boundary    | Output colors should come from the generated palette                        |
| Detail              | Fine image structure should remain legible after recoloring                 |

## Non-goals

- No chezmoi-templated palette rendering.
- No restoration of the old Python wallpaper themer.
- No hand-tuned per-wallpaper palette subsets.
- No contrast gates for LUT generation.
- No automatic wallpaper recoloring triggered by palette changes.

The generator is a one-shot derivation step. The checked-in palette is the
reusable artifact, and visual inspection remains the final rendering check.
