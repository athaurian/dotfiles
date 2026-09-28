# Color scheme: One Dark on Neutral

This document is the single source of truth for desktop colors.

Locked hex values are palette seeds for both modes. Supporting tints are derived
from the specifications below by `meta/palette.py`, which also writes the two
LUT palettes and the active mode's `home/.chezmoidata.yaml`. Application
templates consume the data file's palette tokens; application files may use only
colors that trace back to this document.

## Design

| Principle        | Rule                                                                                                                      |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Neutral grounds  | All grounds use the pure-neutral ramps below, one per mode.                                                               |
| Modes            | Dark and light share role names, chromatics, and derivation formulas; only the neutral ramps differ, and both are locked. |
| Chromatic source | All chromatic hues come from One Dark Pro classic: `refs/onedark-pro/src/themes/themeData.ts`, `textColors.classic`.      |
| Chroma           | One Dark Pro base hues are boosted by `1.5×` at constant lightness and hue.                                               |
| Accent           | `#48AFFF` and `#98C3FF` are the only accent pair.                                                                         |
| Palette boundary | No application-local color inventions. Every application hex must be traceable here.                                      |
| Hierarchy        | Neutral roles remain distinct and monotonic from dark to light.                                                           |
| New hues         | A new hue requires an explicit change to this document before it appears in an application.                               |

The palette deliberately avoids per-application accents and secondary blues.

## NeutralsBoth ramps are locked: the same eleven roles, pure neutral, listed from the

deepest ground role to maximal emphasis. Light `base` (`#EAEAEA`) and `text-max`
(black) are the locked anchors; every other light role is derived, not
hand-picked: `meta/palette.py` solves it for the pure gray matching the dark
ramp's measured WCAG contrast of the same role against dark `base` — crust and
mantle on the lighter side of light base, the surface and text roles on the
darker side — and rewrites those cells on every run. The result is
mode-invariant role semantics: any role pair measures the same contrast in both
modes.

### Dark

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

### Light

| Hex       | Role      | Semantic use                                                          |
| --------- | --------- | --------------------------------------------------------------------- |
| `#FCFCFC` | crust     | deepest editor grounds, such as TabLine and folds                     |
| `#F5F5F5` | mantle    | transient editor chrome, including floats, pickers, and Pmenu         |
| `#EAEAEA` | base      | primary editor, terminal, bar, notification, and window grounds       |
| `#E2E2E2` | surface-0 | cursorline, alternate base, tooltip base                              |
| `#D8D8D8` | surface-1 | hover fills, buttons, menu selection, low-urgency notification ground |
| `#C5C5C5` | surface-2 | borders, selections, btop boxes, indent guides, low-urgency frames    |
| `#999999` | line      | focus borders and subtle dividers                                     |
| `#676767` | muted     | comments, placeholders, disabled text, low-urgency text               |
| `#474747` | subtext   | secondary text, titles, tab labels, dimmed emphasis                   |
| `#303030` | text      | primary text                                                          |
| `#000000` | text-max  | selected, hovered, or otherwise maximal emphasis                      |

`crust` and `mantle` are editor-only depth levels, but remain part of the global
ramp. Neovim must stay within these eleven values per mode.

For Catppuccin slot compatibility, slot names are aliases rather than additional
colors:

| Catppuccin slot        | Repository color |
| ---------------------- | ---------------- |
| `overlay2`, `subtext0` | `muted`          |
| `overlay1`             | `surface-2`      |
| `overlay0`             | `line`           |

These mappings intentionally differ from Catppuccin's upstream hierarchy.

## ChromaticsThe Dark Base column contains the `1.5×` One Dark Pro classic chroma values;

dark Bright values are hand-tuned lighter variants. The Light Base and Light
Bright columns are solved per hue at constant OKLCH hue and chroma: the darkest
lightness reaching 6.0:1 (Base) and 7.5:1 (Bright) WCAG contrast on the light
`base` ground. Bright carries emphasis in both modes — the lighter step on dark
grounds, the darker, higher-contrast step on light grounds — so bold and
highlighted text keeps its prominence. `meta/palette.py` derives them on every
run; their measured values are recorded here.

| Hue    | Dark base | Dark bright | Light base | Light bright | Semantics                                  |
| ------ | --------- | ----------- | ---------- | ------------ | ------------------------------------------ |
| red    | `#FE4864` | `#FF7376`   | `#B10035`  | `#96002B`    | errors, urgency, deleted content, specials |
| green  | `#89C952` | `#B9EE7D`   | `#376200`  | `#2D5300`    | success, added content, strings            |
| yellow | `#F4BC45` | `#FFD678`   | `#725200`  | `#604500`    | warnings, modified content, types          |
| blue   | `#48AFFF` | `#98C3FF`   | `#005B92`  | `#004C7D`    | links, cursor, focus, directories, accent  |
| purple | `#D95AFC` | `#E67FFF`   | `#9400B3`  | `#7D0099`    | keywords, root names                       |
| cyan   | `#00BBCC` | `#3DDAEE`   | `#00616A`  | `#00525A`    | enum members, secondary types              |
| orange | `#E49137` | `#F2A256`   | `#814A00`  | `#6D3E00`    | numbers, properties, dashboard header      |

There are exactly seven hues and one bright step per hue per mode.

The accent pair is `blue` and `blue_bright` within the active mode; light mode
uses its solved values, so accent-on-light text clears the same readability bar
as the rest of the palette.

Each mode's LUT palette and data file use that mode's base and bright columns.
Templates keep one set of color names; the mode decides the values.

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

The Hex columns are generated per mode by `meta/palette.py`. Do not edit
generated hexes by hand.

| Tint             | Anchor    | Hue    | k     | Dark hex                 | Light hex          | Semantic use                                   |
| ---------------- | --------- | ------ | ----- | ------------------------ | ------------------ | ---------------------------------------------- |
| `selection-deep` | n/a       | n/a    | n/a   | `#3A3F4B`                | `#BBC7D2`          | fuzzel and Qt selection                        |
| `on-accent`      | n/a       | n/a    | n/a   | `#202020`                | `#FFFFFF`          | text placed on accent grounds                  |
| `hover`          | n/a       | n/a    | n/a   | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.08)` | bar hover overlay                              |
| warning-hover    | surface-1 | yellow | 0.302 | `#382B11`                | `#E2D7C3`          | Waybar and btop warning hover                  |
| error-hover      | surface-1 | red    | 0.256 | `#452123`                | `#F7CCCD`          | Waybar and btop error hover                    |
| urgent           | surface-1 | red    | 0.35  | `#4C1A1F`                | `#FFC8CA`          | critical notification and urgent-window ground |
| notice           | surface-1 | blue   | 0.35  | `#142F46`                | `#C3DCF2`          | normal notification ground                     |
| selection        | surface-2 | blue   | 0.179 | `#2F3C47`                | `#BBC7D2`          | Neovim Visual and Search                       |
| diff-add         | surface-2 | green  | 0.432 | `#2B4218`                | `#B8CDA9`          | Neovim additions                               |
| diff-change      | surface-2 | blue   | 0.444 | `#183D5A`                | `#AAC9E5`          | Neovim changes                                 |
| diff-delete      | surface-0 | red    | 0.208 | `#391C1E`                | `#FCD8D9`          | Neovim deletions                               |
| diff-text        | line      | blue   | 0.562 | `#2D5E86`                | `#789EBF`          | Neovim changed text                            |

`selection-deep` is intentionally used instead of the derived selection tint for
fuzzel and Qt because the existing rendering is tested and readable.

`on-accent` exists because nvim places text on accent grounds (IncSearch,
cursors, active pills): the base role inverts per mode, so it cannot serve as
the on-accent foreground in light mode.

`hover` and `on-accent` are hand-written; every other row's hex columns are
generated per mode from its anchor ramp.

## Utility colors

| Token         | Value              | Rule                                                                                                                                        |
| ------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `black`       | `#000000`          | Utility black for shadows and other uses outside the neutral ramp. When used as a shadow or line overlay, carry alpha, such as `#00000080`. |
| `transparent` | `rgba(0, 0, 0, 0)` | Fully transparent black overlay for CSS surfaces, such as waybar borders.                                                                   |

## Color semantics

### Neutral hierarchy

- `text-max` is stronger than `text`.
- `text` is stronger than `subtext`.
- `subtext` is stronger than `muted`.
- All four remain visually distinct on either mode's `base`.
- Titles use `subtext`, not `text`.
- Comments use italic `muted`, not an overlay role.

`meta/palette.py check` reports text-role contrast ratios for inspection. Those
reports are informational, not gates.

### Accent usage

The accent pair is limited to named interaction states:

| Accent use                                                     | Treatment                                                       |
| -------------------------------------------------------------- | --------------------------------------------------------------- |
| Links, cursors, cursorline number, match highlights, IncSearch | accent                                                          |
| Info diagnostics and cmdline icon                              | accent                                                          |
| Focused workspace                                              | accent text with transparent background                         |
| Launcher and Qt selection                                      | `selection-deep` with the `text` role                           |
| Normal notification                                            | accent text, or the `notice` ground with the mode's `text` role |
| Active Mason/Lazy pills                                        | accent ground with `on-accent` text                             |

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

## Chezmoi data and templates

`home/.chezmoidata.yaml` is generated by `meta/palette.py` from this document
for the active mode. It holds a `mode` token (`dark` or `light`) and one flat
`palette` map of this document's role names, with dashes written as underscores,
each carrying the formats consumers need: `hex` is `#D4D4D4`, `bare` is
`D4D4D4`, and the alpha overlays carry `rgba`. Application `.tmpl` files bind
`{{ $p := .palette }}` and reference `{{ $p.base.hex }}`; they contain no
literal colors, so the palette boundary holds by construction. Per-usage alpha
suffixes, such as the `FF` in fuzzel grounds or the `80` in sway shadows, stay
in the template lines that use them.

The generated file is machine-local state, not repository content: it is
git-ignored, because the active mode can differ between machines. A fresh clone
runs `make palette` once before `chezmoi apply`. The active mode itself lives in
`~/.local/state/palette-mode` (the same class of state as
`.config/wlsunset.env`: machine-local, never deployed or committed); a missing
file means dark.

Neovim is templated like every other consumer; its locked captures are verified
with `:Inspect`.

### Qt bevel slots

qt5ct palettes map the ramp onto Qt's brightness-absolute bevel slots, which
must ladder `Light >= Midlight >= Button/Window >= Mid >= Dark >= Shadow` in
every mode; an inverted ladder paints raised panels darker than the window. The
doctrine is the cross-mode invariant applied to slots: each slot takes the ramp
role nearest its light-mode WCAG relief against the chrome role (`surface-1`),
clamped to what the mode's ramp offers — where the ramp lacks an intermediate,
slots coalesce. Light: crust, mantle, surface-1, surface-2, line, muted. Dark:
surface-2, surface-1, surface-1, base, base, crust. The qt5ct template
implements the mapping; KeePassXC and other Qt apps render through it.

## Palette boundary and checks`meta/palette.py check` enforces the documentation boundary for static

application files, verifies the generated data and both LUT files match this
document for the active mode, and hard-fails when any named contrast pair in its
gate list falls below its floor in either mode — text, border, accent-on-` fill,
and the per-hue emphasis rule. Template files carry no literal colors, so their
boundary holds by construction.

| Source form                                                      | Detected |
| ---------------------------------------------------------------- | -------- |
| `#hex`, including eight-digit alpha values after stripping alpha | Yes      |
| foot-style bare `key=value` hexadecimal values                   | Yes      |
| Quoted bare hex values                                           | No       |
| `rgba()` values                                                  | No       |

Keep static application configuration in forms covered by the checker.

When changing a color:

1. Update the seed or specification here.
2. Run `make palette` (mode defaults to the machine's mode file; pass
   `MODE=light` or `MODE=dark` to override without switching).
3. Run `chezmoi apply` to re-render the `.tmpl` consumers.
4. Run the checker again.

Switching modes is one command: `make light` or `make dark` records the
machine's mode file, regenerates the palette data, and applies. The run_onchange
mode hook then runs on apply — it writes dconf, re-renders the wallpaper with
the new mode's palette, and reloads the session's consumers last, after all
palette state is written. The hook calls `sw --restore`, which re-applies that
mode's own last-changed wallpaper — recorded per mode by `sw` in `~/.cache/sw` —
so a switch lands on a wallpaper from the mode's pool rather than the previous
mode's last pick.

The LUT palettes follow the same source boundary and are documented separately
in `meta/lut-palette.md`.

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

These captures must resolve to the listed hexes in dark mode; in light mode the
neutral roles (text, muted) follow the light ramp while the chromatic hexes
stay. Catppuccin defaults and explicit overrides are both acceptable; `:Inspect`
is the verification point.

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
- No per-app alias namespaces or semantic role indirection in the data.
- No contrast-gate tooling.
- No GTK theme redesign as part of the palette system.
