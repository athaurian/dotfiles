# Color scheme: One Dark on Neutral

This document is the single source of truth for desktop colors.

Locked hex values are palette seeds. Supporting tints are derived from the
specifications below by `meta/palette.py`. Application files may use only colors
that trace back to this document.

## Design

| Principle        | Rule                                                                                                                 |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| Neutral grounds  | All grounds use the pure-neutral ramp below.                                                                         |
| Chromatic source | All chromatic hues come from One Dark Pro classic: `refs/onedark-pro/src/themes/themeData.ts`, `textColors.classic`. |
| Chroma           | One Dark Pro base hues are boosted by `1.5×` at constant lightness and hue.                                          |
| Accent           | `#48AFFF` and `#98C3FF` are the only accent pair.                                                                    |
| Palette boundary | No application-local color inventions. Every application hex must be traceable here.                                 |
| Hierarchy        | Neutral roles remain distinct and monotonic from dark to light.                                                      |
| New hues         | A new hue requires an explicit change to this document before it appears in an application.                          |

The palette deliberately avoids per-application accents and secondary blues.
Sapphire and maroon are not independent hues. Mauve and lavender are represented
by purple and purple-bright.

## Neutrals

The eleven-step ramp is locked from dark to light.

| Hex       | Role      | Semantic use                                                          |
| --------- | --------- | --------------------------------------------------------------------- |
| `#101010` | crust     | deepest editor grounds, such as TabLine and folds                     |
| `#171717` | mantle    | transient editor chrome, including floats, pickers, and Pmenu         |
| `#202020` | base      | primary editor, terminal, bar, notification, and window grounds       |
| `#262626` | surface-0 | cursorline, alternate base, tooltip base                              |
| `#2D2D2D` | surface-1 | hover fills, buttons, menu selection, low-urgency notification ground |
| `#3A3A3A` | surface-2 | borders, selections, btop boxes, indent guides, low-urgency frames    |
| `#5A5A5A` | line      | focus borders and subtle dividers                                     |
| `#8A8A8A` | muted     | comments, placeholders, disabled text, low-urgency text               |
| `#B3B3B3` | subtext   | secondary text, titles, tab labels, dimmed emphasis                   |
| `#D4D4D4` | text      | primary text                                                          |
| `#FFFFFF` | text-max  | selected, hovered, or otherwise maximal emphasis                      |

`crust` and `mantle` are editor-only depth levels, but remain part of the global
ramp. Neovim must stay within these eleven values.

For Catppuccin slot compatibility, slot names are aliases rather than additional
colors:

| Catppuccin slot        | Repository color      |
| ---------------------- | --------------------- |
| `overlay2`, `subtext0` | `muted` `#8A8A8A`     |
| `overlay1`             | `surface-2` `#3A3A3A` |
| `overlay0`             | `line` `#5A5A5A`      |

These mappings intentionally differ from Catppuccin's upstream hierarchy.

## Chromatics

The Base column contains the `1.5×` One Dark Pro classic chroma values. Bright
values are hand-tuned lighter variants and have no derivation formula.

| Hue    | Base      | Bright    | Semantics                                  |
| ------ | --------- | --------- | ------------------------------------------ |
| red    | `#FE4864` | `#FF7376` | errors, urgency, deleted content, specials |
| green  | `#89C952` | `#B9EE7D` | success, added content, strings            |
| yellow | `#F4BC45` | `#FFD678` | warnings, modified content, types          |
| blue   | `#48AFFF` | `#98C3FF` | links, cursor, focus, directories, accent  |
| purple | `#D95AFC` | `#E67FFF` | keywords, root names                       |
| cyan   | `#00BBCC` | `#3DDAEE` | enum members, secondary types              |
| orange | `#E49137` | `#F2A256` | numbers, properties, dashboard header      |

There are exactly seven hues and one bright step per hue.

The following upstream distinctions are intentionally collapsed:

| Source color     | Repository mapping     |
| ---------------- | ---------------------- |
| sapphire         | blue                   |
| maroon           | red                    |
| flamingo         | red                    |
| pink             | red-bright             |
| teal             | cyan                   |
| sky              | cyan-bright            |
| rosewater        | orange-bright          |
| mauve / lavender | purple / purple-bright |

Do not introduce stock pastel colors or additional chromatic families.

## Supporting tints

A derived tint is defined by:

```text
oklch(anchor L, base C × k, base H)
```

where `anchor` is a neutral ramp role, `base` is one of the chromatic Base
colors, and `k` is a chroma fraction.

The Hex column is generated by `meta/palette.py`. Do not edit generated hexes by
hand.

| Tint             | Anchor    | Hue    | k     | Hex                      | Semantic use                                   |
| ---------------- | --------- | ------ | ----- | ------------------------ | ---------------------------------------------- |
| `selection-deep` | n/a       | n/a    | n/a   | `#3A3F4B`                | fuzzel and Qt selection                        |
| `hover`          | n/a       | n/a    | n/a   | `rgba(255,255,255,0.08)` | bar hover overlay                              |
| warning-hover    | surface-1 | yellow | 0.302 | `#382B11`                | Waybar and btop warning hover                  |
| error-hover      | surface-1 | red    | 0.256 | `#452123`                | Waybar and btop error hover                    |
| urgent           | surface-1 | red    | 0.35  | `#4C1A1F`                | critical notification and urgent-window ground |
| notice           | surface-1 | blue   | 0.35  | `#142F46`                | normal notification ground                     |
| selection        | surface-2 | blue   | 0.179 | `#2F3C47`                | Neovim Visual and Search                       |
| diff-add         | surface-2 | green  | 0.432 | `#2B4218`                | Neovim additions                               |
| diff-change      | surface-2 | blue   | 0.444 | `#183D5A`                | Neovim changes                                 |
| diff-delete      | surface-0 | red    | 0.208 | `#391C1E`                | Neovim deletions                               |
| diff-text        | line      | blue   | 0.562 | `#2D5E86`                | Neovim changed text                            |

`selection-deep` is a retained legacy wash. It is intentionally used instead of
the derived selection tint for fuzzel and Qt because the existing rendering is
tested and readable.

`hover` is the only alpha overlay in this table and remains hand-written.

## Utility colors

| Hex       | Rule                                                                                                                        |
| --------- | --------------------------------------------------------------------------------------------------------------------------- |
| `#000000` | Utility black for shadows and other uses outside the neutral ramp. When used as a shadow, carry alpha, such as `#00000080`. |

## Color semantics

### Neutral hierarchy

- `text-max` is stronger than `text`.
- `text` is stronger than `subtext`.
- `subtext` is stronger than `muted`.
- All four remain visually distinct on `base` `#202020`.
- Titles use `subtext`, not `text`.
- Comments use italic `muted`, not an overlay role.

`meta/palette.py check` reports text-role contrast ratios for inspection. Those
reports are informational, not gates.

### Accent usage

The accent pair is limited to named interaction states:

| Accent use                                                     | Treatment                                          |
| -------------------------------------------------------------- | -------------------------------------------------- |
| Links, cursors, cursorline number, match highlights, IncSearch | accent                                             |
| Info diagnostics and cmdline icon                              | accent                                             |
| Focused workspace                                              | accent text with transparent background            |
| Launcher and Qt selection                                      | `selection-deep` with light text                   |
| Normal notification                                            | accent text or the `notice` ground with light text |
| Active Mason/Lazy pills                                        | accent ground with base text                       |

Do not use bright accent grounds by default.

Neutral interaction surfaces follow the hierarchy instead:

- Picker rows, bar pills, and btop selection use `surface-1`.
- When the surrounding ground is already `surface-1`, use `surface-2`.
- Text selection uses the derived `selection` tint.
- Focus uses a one-step border lift: `line` over `surface-2`.
- Search uses a chromatic treatment, never a plain gray surface.

### Transient chrome

Floats, pickers, and Pmenu use `mantle` with a `surface-2` border. Preview panes
may use `base`.

The only intentional exception is the Snacks terminal, whose transparent surface
remains `bg = "none"` with dimmed foreground when unfocused.

## Palette boundary and checks

`meta/palette.py check` enforces the documentation boundary.

| Source form                                                      | Detected |
| ---------------------------------------------------------------- | -------- |
| `#hex`, including eight-digit alpha values after stripping alpha | Yes      |
| foot-style bare `key=value` hexadecimal values                   | Yes      |
| Quoted bare hex values                                           | No       |
| `rgba()` values                                                  | No       |

Keep application configuration in forms covered by the checker.

When changing a color:

1. Update the seed or specification here.
2. Run `meta/palette.py`.
3. Apply the generated hexadecimal values to consumers.
4. Run the checker again.

The LUT palette follows the same source boundary and is documented separately in
`meta/lut-palette.md`.

## Syntax layer

The following Neovim captures are locked.

| Capture                      | Hex       | Role          |
| ---------------------------- | --------- | ------------- |
| `@keyword`                   | `#D95AFC` | purple        |
| `@function`                  | `#48AFFF` | blue          |
| `@string`                    | `#89C952` | green         |
| `@number`, `@constant`       | `#E49137` | orange        |
| `@type`                      | `#F4BC45` | yellow        |
| `@variable`                  | `#D4D4D4` | text          |
| `@variable.parameter`        | `#D4D4D4` | text          |
| special, `@variable.builtin` | `#FE4864` | red           |
| `@property`, members         | `#E49137` | orange        |
| enum member                  | `#00BBCC` | cyan          |
| `@operator`                  | `#00BBCC` | cyan          |
| `@comment`                   | `#8A8A8A` | muted, italic |

These captures must resolve to the listed hexes. Catppuccin defaults and
explicit overrides are both acceptable; `:Inspect` is the verification point.

Chrome-only `custom_highlights` may remain outside this semantic table.

### Deliberate deviations from One Dark Pro

| Capture                 | Repository decision | Reason                                                                 |
| ----------------------- | ------------------- | ---------------------------------------------------------------------- |
| `@property` and members | orange              | Unified treatment instead of language-dependent red/yellow/gray splits |
| `@variable.builtin`     | red                 | Keeps built-in variables in the special-value family                   |
| `@variable`             | text gray           | Matches the desired rendered appearance                                |
| punctuation             | muted               | Reduces visual weight by one neutral step                              |
| warnings                | yellow              | Keeps warnings aligned with the repository's semantic yellow           |

## Non-goals

- No separate palette builder or `palettes/` hierarchy.
- No contrast-gate tooling.
- No `.tmpl` color variables.
- No GTK theme redesign as part of the palette system.

The generator derives supporting tints and LUT data. This document remains the
seed and semantic source of truth.
