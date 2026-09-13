# Palette system

The palette is the single source of truth for every color in this setup. The
files live in `palettes/flint/`:

```
palettes/flint/
├── shared.yaml    # Roles, ANSI slots, Catppuccin aliases, app namespaces, alpha rules, contrast floors, LUT palettes, desktop metrics
├── dark.yaml      # Flint hex values, dark-specific overrides, the Qt bevel ladder
└── light.yaml     # Sand hex values, light-specific overrides, the Qt bevel ladder
```

Two terms cover the whole system:

- A _raw token_ is a named color value, the hex itself like `#1c1c1c`.
- A _semantic role_ is a named job a color does, like `background` or
  `focus_border`. Roles point at tokens, and the same role can point at
  different tokens in different variants.

`scripts/build_palette_data.py` validates the palette, computes every derived
format, and writes `.chezmoidata.yaml` into `home/`. When `chezmoi apply` runs,
chezmoi makes the colors available to every `.tmpl` file. Changing a color takes
the same steps every time: edit a palette file, run the build, apply with
chezmoi.

## Ground truth

The hex values track the current Obsidian variable reference
(`docs.obsidian.md`, Foundations/Colors): the dark ramp starts at base-00
`#1c1c1c`, not the older `#1e1e1e` app.css snapshot, and the dark
`selection_wash` is pinned at 33% (`0x54`) over the Qt base, verified against
the app itself, rather than the older 25%. Where a variant deviates from the
official hex (the deepened light accent and hues), the deviation is a contrast
adaptation so the existing 4.5:1 rows keep passing.

One official token is deliberately uncovered: `--text-highlight-bg` (the
`<mark>` fill) has no desktop counterpart here, and search matches already have
the `search_bg` and `inc_search_bg` roles, so no `mark` token exists.

## Accessibility

The palette is an implementation of WCAG AA 2.2 for the role pairs listed in
`contrast_checks` in `shared.yaml`. Body text must clear 4.5:1 against its
background (SC 1.4.3), and boundaries and meaningful graphics must clear 3:1
against their adjacent color (SC 1.4.11). A few shading pairs carry lower house
floors, marked as house rules in the file, because the 3:1 floor would force
artifacts such as striped panels. The validator runs on every build and aborts
when a listed pair falls below its floor. Passing the listed pairs does not make
this setup WCAG conformant, since conformance applies to full pages and
processes.

## The accent

Each variant carries exactly one accent, expressed through the semantic roles
`accent`, `accent_text`, `accent_bright`, `accent_strong`, `selection`, and
`on_selection`. The roles cooperate: accent text stays readable on the
background at 4.5:1, accent fills clear 3:1 as graphics, and selection text
clears 4.5:1 on the selection fill. Pointing `accent` at a single token breaks
at least one of the three.

Window borders are deliberately split from the accent. `focus_border` follows
the neutral gray in both variants, and `window_focused_border` follows it in
Flint and the near-black `text` in Sand, so frames stay neutral against any
wallpaper.

## What the build derives

Each raw token is exported in the formats templates need:

- `.hex` is `#1c1c1c`, the standard six-digit form.
- `.bare` is `1c1c1c`, without the hash. The foot terminal and Qt5ct and Qt6ct
  use it.
- `.triple` is `28 28 28`, space-separated RGB, for Zellij KDL.
- `.bare_ff` is `1c1c1cff`, with the alpha channel, for fuzzel and swaylock.

Alpha tokens are transparent overlays, derived from `[base_token, alpha]` rules
in `shared.yaml`. Their `.hex` and `.bare` forms are 8-digit hex for apps that
parse alpha, such as swaylock and zathura, and their `.rgba` form is a CSS
`rgba(r, g, b, a)` string for Waybar.

## Template usage

The export contains both variants. `flint.dark` and `flint.light` hold the
per-variant data, so apps that render both variants at once, like the foot
terminal, read both blocks in one file. The sections under `flint` (`resolved`,
`ansi_resolved`, and `catppuccin_resolved`) alias the active variant, so most
templates read `.flint.resolved` and follow `make dark` and `make light` without
changes:

```ini
# Pattern from home/dot_config/swaylock/config.tmpl
#{{ $c := .flint.resolved }}

ring-color={{ $c.swaylock_ring.bare_ff }}
inside-color={{ $c.background.bare_ff }}
text-color={{ $c.text.bare }}
```

For the switch commands, see [Switch variants](theming.md#switch-variants).
