# Palette system

Colors are defined only in `meta/color-scheme.md`. `make palette` runs
`meta/palette.py`, which regenerates `home/.chezmoidata.yaml` and the _look-up
table (LUT)_ palettes under `home/dot_config/lutgen/`. The `make dark` and
`make light` targets regenerate the same files and apply the configuration in
one step. Never hand-edit the generated files.
