# Color scheme: One Dark on Neutral

This document is the source of truth for every color in the repository, and
`meta/palette.py` reads its tables to generate the palette data. Grounds, the
background colors, come from one pure-gray neutral ramp per mode. Hues come from
One Dark Pro, a color theme for Visual Studio Code, and the tints and syntax
colors derive from those two sets.

## Design

The following table states the design rules for the palette:

| Principle        | Rule                                                                                                                      |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Neutral grounds  | All grounds use the pure-neutral ramps below, one per mode.                                                               |
| Modes            | Dark and light share role names, chromatics, and derivation formulas. Only the neutral ramps differ, and both are locked. |
| Chromatic source | All chromatic hues come from One Dark Pro classic: `refs/onedark-pro/src/themes/themeData.ts`, `textColors.classic`.      |
| Chroma           | One Dark Pro base hues are boosted by `1.5×` in chroma, a measure of color intensity, at constant lightness and hue.      |
| Accent           | `#48AFFF` and `#98C3FF` are the only accent pair.                                                                         |
| Palette boundary | No application-local color inventions. Every application hex must be traceable here.                                      |
| Hierarchy        | Neutral roles remain distinct and monotonic from dark to light.                                                           |
| New hues         | A new hue requires an explicit change to this document before it appears in an application.                               |

## Neutrals

The neutrals are pure grays, one ramp per mode, and every ground color in the
system comes from them. Each row pairs a hex value with a role, a name for where
that color is used.

### Dark

The following table lists the dark ramp from the deepest ground to maximal
emphasis:

| Hex       | Role      | Semantic use                                                          |
| --------- | --------- | --------------------------------------------------------------------- |
| `#101010` | crust     | Deepest editor grounds, such as TabLine and folds                     |
| `#171717` | mantle    | Transient editor chrome, including floats, pickers, and Pmenu         |
| `#202020` | base      | Primary editor, terminal, bar, notification, and window grounds       |
| `#262626` | surface-0 | Cursorline, alternate base, tooltip base                              |
| `#2D2D2D` | surface-1 | Hover fills, buttons, menu selection, low-urgency notification ground |
| `#3A3A3A` | surface-2 | Borders, selections, btop boxes, indent guides, low-urgency frames    |
| `#5A5A5A` | line      | Focus borders and subtle dividers                                     |
| `#8A8A8A` | muted     | Comments, placeholders, disabled text, low-urgency text               |
| `#B3B3B3` | subtext   | Secondary text, titles, tab labels, dimmed emphasis                   |
| `#D4D4D4` | text      | Primary text                                                          |
| `#FFFFFF` | text-max  | Selected, hovered, or otherwise maximal emphasis                      |

### Light

The following table lists the light ramp in the same role order:

| Hex       | Role      | Semantic use                                                          |
| --------- | --------- | --------------------------------------------------------------------- |
| `#FCFCFC` | crust     | Deepest editor grounds, such as TabLine and folds                     |
| `#F5F5F5` | mantle    | Transient editor chrome, including floats, pickers, and Pmenu         |
| `#EAEAEA` | base      | Primary editor, terminal, bar, notification, and window grounds       |
| `#E2E2E2` | surface-0 | Cursorline, alternate base, tooltip base                              |
| `#D8D8D8` | surface-1 | Hover fills, buttons, menu selection, low-urgency notification ground |
| `#C5C5C5` | surface-2 | Borders, selections, btop boxes, indent guides, low-urgency frames    |
| `#999999` | line      | Focus borders and subtle dividers                                     |
| `#676767` | muted     | Comments, placeholders, disabled text, low-urgency text               |
| `#474747` | subtext   | Secondary text, titles, tab labels, dimmed emphasis                   |
| `#303030` | text      | Primary text                                                          |
| `#000000` | text-max  | Selected, hovered, or otherwise maximal emphasis                      |

The following table maps Catppuccin, a community color scheme, to the repository
roles that correspond to its palette slots:

| Catppuccin slot        | Repository color |
| ---------------------- | ---------------- |
| `overlay2`, `subtext0` | `muted`          |
| `overlay1`             | `surface-2`      |
| `overlay0`             | `line`           |

## Chromatics

The following table lists the hues, their hex values in both modes, and their
semantics:

| Hue    | Dark base | Dark bright | Light base | Light bright | Semantics                                  |
| ------ | --------- | ----------- | ---------- | ------------ | ------------------------------------------ |
| red    | `#FE4864` | `#FF7376`   | `#B10035`  | `#96002B`    | Errors, urgency, deleted content, specials |
| green  | `#89C952` | `#B9EE7D`   | `#376200`  | `#2D5300`    | Success, added content, strings            |
| yellow | `#F4BC45` | `#FFD678`   | `#725200`  | `#604500`    | Warnings, modified content, types          |
| blue   | `#48AFFF` | `#98C3FF`   | `#005B92`  | `#004C7D`    | Links, cursor, focus, directories, accent  |
| purple | `#D95AFC` | `#E67FFF`   | `#9400B3`  | `#7D0099`    | Keywords, root names                       |
| cyan   | `#00BBCC` | `#3DDAEE`   | `#00616A`  | `#00525A`    | Enum members, secondary types              |
| orange | `#E49137` | `#F2A256`   | `#814A00`  | `#6D3E00`    | Numbers, properties, dashboard header      |

The following table states the repository hue for each Catppuccin color:

| Catppuccin color | Repository mapping     |
| ---------------- | ---------------------- |
| sapphire         | blue                   |
| maroon           | red                    |
| flamingo         | red                    |
| pink             | red-bright             |
| teal             | cyan                   |
| sky              | cyan-bright            |
| rosewater        | orange-bright          |
| mauve / lavender | purple / purple-bright |

## Supporting tints

The following table lists the supporting tints. Anchor names the neutral role
that supplies a tint's lightness, Hue names the chromatic hue that supplies its
color, and k is the fraction of that hue's chroma the tint keeps. A row with
`n/a` in those three columns is hand-written rather than derived.

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

## Utility colors

The following table lists the utility colors that fall outside the neutral ramp
and how to use them:

| Token         | Value              | Rule                                                                                                                                        |
| ------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `black`       | `#000000`          | Utility black for shadows and other uses outside the neutral ramp. When used as a shadow or line overlay, carry alpha, such as `#00000080`. |
| `transparent` | `rgba(0, 0, 0, 0)` | Fully transparent black overlay for CSS surfaces, such as Waybar borders.                                                                   |

## Color semantics

### Accent usage

The following table states the treatment for each accent use:

| Accent use                                                     | Treatment                                                       |
| -------------------------------------------------------------- | --------------------------------------------------------------- |
| Links, cursors, cursorline number, match highlights, IncSearch | accent                                                          |
| Info diagnostics and cmdline icon                              | accent                                                          |
| Focused workspace                                              | accent text with transparent background                         |
| Launcher and Qt selection                                      | `selection-deep` with the `text` role                           |
| Normal notification                                            | accent text, or the `notice` ground with the mode's `text` role |
| Active Mason/Lazy pills                                        | accent ground with `on-accent` text                             |

## Palette boundary and checks

The following table lists each color form in the configuration files and whether
the palette check detects it:

| Source form                                                      | Detected |
| ---------------------------------------------------------------- | -------- |
| `#hex`, including eight-digit alpha values after stripping alpha | Yes      |
| Foot-style bare `key=value` hexadecimal values                   | Yes      |
| Quoted bare hex values                                           | No       |
| `rgba()` values                                                  | No       |

## Syntax layer

The following table maps each syntax capture to its repository role:

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

### Deliberate deviations from One Dark Pro

The following table states the repository decision and reason for each capture
that differs from One Dark Pro:

| Capture                 | Repository decision | Reason                                                                 |
| ----------------------- | ------------------- | ---------------------------------------------------------------------- |
| `@property` and members | orange              | Unified treatment instead of language-dependent red/yellow/gray splits |
| `@variable.builtin`     | red                 | Keeps built-in variables in the special-value family                   |
| `@variable`             | text gray           | Matches the desired rendered appearance                                |
| punctuation             | muted               | Reduces visual weight by one neutral step                              |
| warnings                | yellow              | Keeps warnings aligned with the repository's semantic yellow           |
