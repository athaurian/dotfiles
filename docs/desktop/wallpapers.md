# Wallpapers (`sw`)

| Property       | Value                              |
| :------------- | :--------------------------------- |
| Entry point    | `sw`                               |
| Implementation | `home/dot_local/bin/executable_sw` |

Wallpapers are managed in three independent stages. Any stage can be invoked on
its own.

| Stage   | Behavior                                                                                                                |
| :------ | :---------------------------------------------------------------------------------------------------------------------- |
| Select  | Takes the next or previous image from `~/Pictures/Wallpapers/pool_dark` or `pool_light`                                 |
| Recolor | Matches the active palette with [`lutgen`](../glossary.md#lutgen) and a generated [Hald CLUT](../glossary.md#hald-clut) |
| Apply   | Sets the result with `awww` on Wayland (`thinkpad`) or `feh` on X11 (`optiplex`)                                        |

## Commands

```bash
sw --next              # advance to the next wallpaper in the queue and set it
sw --prev              # go back to the previous wallpaper and set it
sw --restore           # re-apply the recorded wallpaper without rotating (used on theme switch)
sw IMAGE               # recolor an image into the output directory
sw IMAGE --set         # recolor an image and set it as the wallpaper
```

## Recoloring and caching

Since recoloring a high-resolution image is expensive on the first pass, both
the [color lookup table](../glossary.md#clut) and the rendered image are cached.
A cached render is valid only while its inputs are unchanged, hence the cache
key is built from:

- the source image content,
- the resolved palette,
- the `lutgen` parameters.

Returning to a previously viewed wallpaper reuses the cached render, and
switching modes applies the cached render when one exists for that mode.

| Cache           | Path                             |
| :-------------- | :------------------------------- |
| Generated LUTs  | `$XDG_CACHE_HOME/sw/luts/`       |
| Rendered images | `$XDG_CACHE_HOME/sw/wallpapers/` |

## Options and environment overrides

CLI flags override the corresponding environment variables.

| Option             | Environment variable                              | Default                         | Description                                      |
| :----------------- | :------------------------------------------------ | :------------------------------ | :----------------------------------------------- |
| `-p, --palette`    | `SW_PALETTE`                                      | `neutral` (`neutral-light`)     | `lutgen` palette name or path                    |
| `-l, --lum`        | `SW_LUM`                                          | `1.05`                          | Luminosity factor passed to `lutgen`             |
| `--blur`           | —                                                 | Off                             | Use Gaussian blur instead of RBF                 |
| `-r, --radius`     | `SW_RADIUS`                                       | `8.0`                           | Gaussian blur radius, blur mode only             |
| `-s, --shape`      | `SW_SHAPE`                                        | `96.0`                          | Gaussian RBF shape, RBF mode only                |
| `--no-preserve`    | `SW_PRESERVE=0`                                   | Preserve on                     | Do not preserve original luminosity and contrast |
| `--refresh`        | —                                                 | Off                             | Regenerate the cached LUT and reapply            |
| `-o, --output-dir` | —                                                 | `$XDG_CACHE_HOME/sw/wallpapers` | Output directory for rendered images             |
| `--pool-dir`       | —                                                 | `pool_{dark,light}`             | Rotation pool directory                          |
| `--set`            | —                                                 | Off                             | Set the last rendered image as the wallpaper     |
| —                  | `SW_MODE`                                         | `~/.local/state/palette-mode`   | Palette variant (`dark` or `light`)              |
| —                  | [`XDG_CACHE_HOME`](../glossary.md#xdg_cache_home) | `~/.cache`                      | Base directory for LUT and render caches         |
