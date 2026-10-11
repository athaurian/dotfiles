# Palette system

Colors are defined only in
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml).
Every other color in the system derives from that file.

The palette comes in two modes, dark and light, and every color has a dark value
and a light value. The active mode decides which values the entire desktop uses.

The [`Makefile`](https://github.com/athaurian/dotfiles/blob/main/Makefile) owns
regeneration and application:

- `palette` regenerates the derived palette data without applying anything.
- `dark` and `light` regenerate the same data and apply the configuration in the
  chosen mode.

The derived output includes
[`home/.chezmoidata.yaml`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoidata.yaml)
and the look-up table (LUT) palettes under
[`home/dot_config/lutgen/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/lutgen/).
Never hand-edit those files. For the exact recipe, read the `palette`, `dark`,
and `light` targets in the `Makefile` and the
[`meta/palette.py`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.py)
script.
