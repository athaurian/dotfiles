# Palette system

Colors are defined only in `meta/color-scheme.md`. Every other color in the
system derives from that file.

The Makefile owns regeneration and application:

- `palette` regenerates the derived palette data without applying anything.
- `dark` and `light` regenerate the same data and apply the configuration in the
  chosen mode.

The derived output includes `home/.chezmoidata.yaml` and the look-up table (LUT)
palettes under `home/dot_config/lutgen/`. Never hand-edit those files. For the
exact recipe, read the `palette`, `dark`, and `light` targets in the Makefile
and the `meta/palette.py` script.
