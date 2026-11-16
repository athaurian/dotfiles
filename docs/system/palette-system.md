# Palette system

Almost all desktop colors derive from a single source file: `meta/palette.toml`.
It defines semantic tokens (backgrounds, foregrounds, borders, accents, and ANSI
terminal slots) for both `dark` and `light` modes.

<figure class="screenshot">
  <img src="../images/palette.webp" alt="A reference card showing every palette color token and hex value for dark and light modes.">
  <figcaption>Every palette value in both modes.</figcaption>
</figure>

## Generating and applying palettes

| Command                               | Action                                                                                                                                                                                                                  |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `make dark` / `make light`            | Generates palette artifacts for the chosen mode, updates `~/.local/state/palette-mode`, runs `chezmoi apply`, reloads live apps (`kitty`, `nvim`, Waybar/Polybar, `dunst`), and recolors the active wallpaper via `sw`. |
| `make palette MODE=dark` (or `light`) | Regenerates the templated palette files and Hald CLUT lookup tables inside the repository **without** applying them to the live session or switching `~/.local/state/palette-mode`.                                     |
| `make shots`                          | Automates switching modes and capturing fresh documentation screenshots.                                                                                                                                                |

### Generated files (do not edit by hand)

Running `make palette` writes:

- `home/dot_config/lutgen/*.png`: Hald CLUT images used by
  [`sw`](../desktop/wallpapers.md) to recolor wallpapers to the current theme.
- `meta/lut-palette.md`: Reference swatch table of the active LUT colors.

Always edit `meta/palette.toml` and re-run `make palette` (or `make dark` /
`make light`) rather than modifying those files directly.

## Intentional exceptions outside `meta/palette.toml`

Four places use fixed colors rather than changing with the palette:

1. **Shell prompt (`PS1`)**: Uses standard terminal ANSI color slots (`1–7`),
   which automatically adapt when `kitty` reloads its terminal palette.
2. **Lock screen fallback fill**: Uses pure black (`#000000`) behind the lock
   image so monitors with different aspect ratios do not glow around the edges
   in a dark room.
3. **Palette preview card background**: Uses a fixed neutral backdrop so dark
   and light swatches can be compared side by side without optical contrast
   shifts.
4. **Documentation site theme**: Managed separately through
   [`docs-theme`](https://github.com/athaurian/docs-theme) so the web docs
   remain readable independent of desktop tweaks.
