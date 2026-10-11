# Color scheme: One Dark on Neutral

`meta/palette.toml` is the source of truth for every color in the repository,
and `meta/palette.py` derives the palette data from it. This document describes
the system. Grounds, the background colors, come from one pure-gray neutral ramp
per mode. Hues come from One Dark Pro, a color theme for Visual Studio Code, and
the tints and syntax colors derive from those two sets.

## Design

The following table states the design rules for the palette:

| Principle        | Rule                                                                                                                                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Neutral grounds  | All grounds use the pure-neutral ramps in `meta/palette.toml`, one per mode.                                                                                                                                |
| Modes            | Dark and light share role names and chromatics. The dark neutral ramp is locked; the light ramp derives from it by holding each role's contrast ratio to `base`, with light `base` and `text-max` hand-set. |
| Chromatic source | All chromatic hues come from One Dark Pro classic: `refs/onedark-pro/src/themes/themeData.ts`, `textColors.classic`.                                                                                        |
| Chroma           | One Dark Pro base hues are boosted by `1.5×` in chroma, a measure of color intensity, at constant lightness and hue.                                                                                        |
| Accent           | Blue is the only accent hue, and its bright step is the accent pair.                                                                                                                                        |
| Palette boundary | No application-local color inventions. Every application hex must be traceable to `meta/palette.toml`.                                                                                                      |
| Hierarchy        | Neutral roles remain distinct and monotonic from dark to light.                                                                                                                                             |
| New hues         | A new hue requires an explicit change to `meta/palette.toml` before it appears in an application.                                                                                                           |

## Neutrals

The neutrals are pure grays, one ramp per mode, and every ground color in the
system comes from them. The dark ramp runs from `crust`, the deepest ground,
through `base` to `text-max`, maximal emphasis; each role carries its semantic
use in `meta/palette.toml`. The light ramp shares the role names and derives
from the dark ramp by holding each role's contrast ratio to `base`; the light
`base` and `text-max` values are hand-set anchors.

The following table maps Catppuccin, a community color scheme, to the repository
roles that correspond to its palette slots:

| Catppuccin slot        | Repository color |
| ---------------------- | ---------------- |
| `overlay2`, `subtext0` | `muted`          |
| `overlay1`             | `surface-2`      |
| `overlay0`             | `line`           |

## Chromatics

The seven hues are red, green, yellow, blue, purple, cyan, and orange, each with
a dark and a light value plus a brighter companion step, locked as data in
`meta/palette.toml` together with its semantics. Blue is the accent hue, and
bright blue is its accent pair.

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

A supporting tint is either hand-written, with explicit dark and light values,
or derived: anchor names the neutral role that supplies its lightness, hue names
the chromatic that supplies its color, and k is the fraction of that hue's
chroma the tint keeps. The tint table in `meta/palette.toml` holds the specs and
each tint's semantic use; `meta/palette.py` computes the derived values.

## Utility colors

Utility colors fall outside the neutral ramp: black for shadows and other
overlays, which carries alpha in that role, and fully transparent black for CSS
surfaces such as Waybar borders.

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

`make palette` fails when a configuration file carries a hex that
`meta/palette.toml` does not list. The following table lists each color form in
the configuration files and whether the palette check detects it:

| Source form                                                      | Detected |
| ---------------------------------------------------------------- | -------- |
| `#hex`, including eight-digit alpha values after stripping alpha | Yes      |
| Foot-style bare `key=value` hexadecimal values                   | Yes      |
| Quoted bare hex values                                           | No       |
| `rgba()` values                                                  | No       |

## Syntax layer

The following table maps each syntax capture to its repository role:

| Capture                      | Role          |
| ---------------------------- | ------------- |
| `@keyword`                   | purple        |
| `@function`                  | blue          |
| `@string`                    | green         |
| `@number`, `@constant`       | orange        |
| `@type`                      | yellow        |
| `@variable`                  | text          |
| `@variable.parameter`        | text          |
| special, `@variable.builtin` | red           |
| `@property`, members         | orange        |
| enum member                  | cyan          |
| `@operator`                  | cyan          |
| `@comment`                   | muted, italic |

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
