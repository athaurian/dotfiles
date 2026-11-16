# Wallpapers (`sw`)

`sw` (`home/dot_local/bin/sw`) rotates wallpapers from
`~/Pictures/Wallpapers/pool_dark` and `pool_light`, recolors each image to match
the active palette using `lutgen` and a generated Hald CLUT, and applies the
result with `awww` on Wayland (`thinkpad`) or `feh` on X11 (`optiplex`).

## Commands

```bash
sw --next              # advance to the next wallpaper in the queue and set it
sw --prev              # go back to the previous wallpaper and set it
sw --restore           # re-apply the recorded wallpaper without rotating (used on theme switch)
sw IMAGE               # recolor an image into the output directory
sw IMAGE --set         # recolor an image and set it as the wallpaper
```

## Recoloring and caching

Recoloring a high-resolution image with `lutgen` takes noticeable CPU time on
first run. `sw` caches generated Hald CLUTs under `$XDG_CACHE_HOME/sw/luts/` and
rendered images under `$XDG_CACHE_HOME/sw/wallpapers/`, keyed by the source
image content, the resolved palette, and the `lutgen` parameters. Switching back
to a previously viewed wallpaper, or between dark and light modes, applies the
cached render immediately.

## Options and environment overrides

CLI flags override the corresponding environment variables.

| Option             | Environment variable | Default                         | Description                                      |
| :----------------- | :------------------- | :------------------------------ | :----------------------------------------------- |
| `-p, --palette`    | `SW_PALETTE`         | `neutral` (`neutral-light`)     | `lutgen` palette name or path                    |
| `-l, --lum`        | `SW_LUM`             | `1.05`                          | Luminosity factor passed to `lutgen`             |
| `--blur`           | —                    | Off                             | Use Gaussian blur instead of RBF                 |
| `-r, --radius`     | `SW_RADIUS`          | `8.0`                           | Gaussian blur radius, blur mode only             |
| `-s, --shape`      | `SW_SHAPE`           | `96.0`                          | Gaussian RBF shape, RBF mode only                |
| `--no-preserve`    | `SW_PRESERVE=0`      | Preserve on                     | Do not preserve original luminosity and contrast |
| `--refresh`        | —                    | Off                             | Regenerate the cached LUT and reapply            |
| `-o, --output-dir` | —                    | `$XDG_CACHE_HOME/sw/wallpapers` | Output directory for rendered images             |
| `--pool-dir`       | —                    | `pool_{dark,light}`             | Rotation pool directory                          |
| `--set`            | —                    | Off                             | Set the last rendered image as the wallpaper     |
| —                  | `SW_MODE`            | `~/.local/state/palette-mode`   | Palette variant (`dark` or `light`)              |
| —                  | `XDG_CACHE_HOME`     | `~/.cache`                      | Base directory for LUT and render caches         |
