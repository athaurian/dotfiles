# LUT palette plan: mathematically colorizing wallpapers to the locked palette

Goal: recolor wallpapers so they match the locked desktop palette
(`meta/color-scheme.md`) — mathematically, via lutgen, not by hand. The old flow
(a 400-line Python themer plus chezmoi-templated "balanced" palette subsets,
`~/.local/bin/flint-wallpaper`) is deliberately not restored; its hand-tuned
subset is what made recolored wallpapers look off. What replaces it: the locked
palette plus mathematically derived intermediate colors, fed to lutgen's
interpolation.

## lutgen mechanics (verified locally, v1.1.1)

- Custom palettes: `~/.config/lutgen/<name>`, one hex per line, with or without
  `#`. Resolved by `-p <name>`.
- Interpolation algorithms: default Gaussian blur (`-r RADIUS`, sigma), Gaussian
  RBF (`-R -s SHAPE -n NEAREST`), Shepard's method, nearest neighbor (`-N`,
  posterizes).
- `-P` preserves the image's original luminance after interpolation; `-L FACTOR`
  weights matching toward colorful or greyscale; both are how the recolor keeps
  image detail instead of washing it out.
- `-l LEVEL` is the Hald CLUT level (default 10); 16 stores the entire sRGB
  space.
- `lutgen apply -p <pal> [flags] img.png -o out.png` generates the LUT and
  applies it in one shot. `lutgen generate` alone writes the Hald CLUT to the
  CWD by default — always pass `-o` explicitly. There is no built-in LUT cache
  directory; any cache is ours to manage.

## The LUT palette

Base (source of truth, `meta/color-scheme.md`): the 11-step neutral ramp
(`#101010` … `#FFFFFF`), the 7 chromatic hues, and their 7 bright steps — 25
locked colors. Nothing outside that doc.

### The generated colors (the "other colors")

25 colors alone posterize photographic images — smooth sky gradients would band
onto the nearest 4–5 stops. So the palette file gains intermediates, derived
mathematically in OKLCH (perceptual space, so interpolation follows how eyes see
lightness/chroma):

1. **Neutral ramp fill.** Linear OKLCH interpolation between adjacent locked
   ramp steps: for steps `A`, `B`, emit `A + i/(N+1) * (B - A)` in OKLCH for
   `i = 1..N`. This turns the 11-step ramp into a smooth gradient every
   greyscale pixel can land on.
2. **Chromatic tints/shades.** For each of the 7 hues, take the hue's OKLCH
   chroma `C` and hue angle `H`, then emit colors at each neutral ramp
   lightness: `oklch(L_ramp, C * (1 - |L_ramp - L_hue| * k), H)` — lightness
   from the ramp, chroma falling off toward black/white so the tints stay
   tasteful at the extremes. `N` and `k` are the two knobs; start at `N = 2`,
   `k = 0.5`.
3. **Output.** The generator writes `home/dot_config/lutgen/neutral` (locked
   colors first, then generated, sorted by lightness) as static hex — checked
   in, re-runnable, never hand-edited. The formula is the documentation; the
   file is the artifact.

The generator is one small script (a Python one-liner class), not a palette
builder: no chezmoi templates, no contrast gates, no YAML. It reads the locked
hexes, computes, writes the file.

## Parameters (starting point)

```
lutgen apply -p neutral -R -s 96 -n 16 -l 10 -P -L 1.05 img.png -o out.png
```

- `-R -s 96` Gaussian RBF, shape 96: the old tested values — smooth blending
  with limited bleeding between distant hues.
- `-n 16` nearest 16 (lutgen default): blends against the 16 closest palette
  colors.
- `-l 10` Hald level 10: enough resolution for photography.
- `-P` preserve luminance: image detail survives the recolor.
- `-L 1.05` slight saturation preference, paired with `-P`.

These carried over from the old flow because they were tuned on real wallpapers;
live with them (rule 1) and adjust one flag at a time. Shape/lum are the two
knobs most likely to need retuning for the neutral palette.

## File layout

- `home/dot_config/lutgen/neutral` — the LUT palette (static hex, generated
  artifact).
- LUT outputs: always `-o ~/.cache/lutgen/neutral.png` — `generate` defaults to
  the CWD and litters otherwise.
- Recolored wallpapers: `~/Pictures/Wallpapers/neutral/`, set via `awww img`
  (sway's wallpaper exec points at the recolored output once wired).

## Workflow

1. Edit a locked color in `meta/color-scheme.md` → re-run the generator → the
   palette file updates.
2. `lutgen apply -p neutral -R -s 96 -n 16 -l 10 -P -L 1.05 ~/Pictures/Wallpapers/dark/flower-basket.jpg -o ~/.cache/lutgen/x.png`
3. `awww img` the output. Eyeball, tune flags, repeat.

## Non-goals

- No chezmoi-templated palette rendering (the old `flint.tmpl` mechanism).
- No Python themer.
- No contrast gates.
- No automatic recolor-on-palette-change machinery. The generator is a one-shot
  command; the palette file is a checked-in artifact; eyeballing is the gate.
