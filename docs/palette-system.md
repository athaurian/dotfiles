# Palette system

Every color in this repository comes from one file:
[`meta/color-scheme.md`](../meta/color-scheme.md). It defines the neutral ramp,
the accent, the semantic roles, and the derived blends, and it is the only place
a color value is written by hand.

## What derives from it

`make palette` runs `meta/palette.py`, which validates the definitions and
writes:

- `home/.chezmoidata.yaml` — the palette every chezmoi template reads at apply
  time. It is gitignored because it regenerates per mode.
- The two LUT palettes under `home/dot_config/lutgen/`, documented in
  [`meta/lut-palette.md`](../meta/lut-palette.md), which the wallpaper helper
  uses to recolor images.

`make light` and `make dark` record the mode file, regenerate both outputs, and
apply in one step.

## Rules

Edit colors only in `meta/color-scheme.md`, then run `make palette` (or a mode
target) and apply. Never hand-edit the generated files — the generator is the
source of truth for them, and `make palette` verifies the derived values.

For how the palette reaches each config, see [Theming](theming.md).
