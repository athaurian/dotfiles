# Palette system

Updating colors across dozens of configuration files was tedious, so the palette uses a single source of truth for the entire desktop.

This section explains how the palette system works. It covers how the files are organized, what the build script derives from them, why the colors stay readable, and how templates pull values out at apply time. It is written for people who are new to this kind of setup, so every term is defined the first time it appears.

## Overview

The palette files live in `palettes/flint/`:

```
palettes/flint/
├── shared.yaml    # Functional roles, ANSI slots, Catppuccin aliases, app namespaces, alpha rules, contrast rules, desktop metrics
├── dark.yaml      # Flint raw hex values, dark-specific overrides, the Qt bevel ladder
└── light.yaml     # Sand raw hex values, light-specific overrides, the Qt bevel ladder
```

Before touching the files, learn two terms:

- A **raw token** is a named color value, the actual hex like `#303030`.
- A **semantic role** is a named job a color does, like `background` or `focus_border`. Roles point at tokens, and the same role can point at different tokens in different variants.

`scripts/build_palette_data.py` validates the palette, computes all necessary formats and alpha blends, and writes `.chezmoidata.yaml` into `home/`. When you run `chezmoi apply`, chezmoi reads that file and injects the colors into any `.tmpl` configuration.

The flow is the same every time. Edit a palette file, run the build script, and apply with chezmoi. The sections that follow trace the same flow, from the files to the derived data to the checks that catch mistakes.

## How the files are structured

### The `shared.yaml` file

This file defines everything that is not tied to a specific color variant:

- **`semantic`.** Functional names that map roles to raw tokens, like `background: bg`, `accent_text: accent_blue_bright`, and `focus_border: overlay_strong`. Your configs mostly consume these semantic roles.
- **`apps`.** App-specific roles, namespaced per application. Each entry `apps.<app>.<key>` becomes the flat role `<app>_<key>` at load time, so `apps.qt.base` turns into the role `qt_base`. This keeps new applications from polluting the core role vocabulary.
- **`ansi`.** The standard 16-color terminal slots (`black`, `red`, `green`, and the rest). ANSI colors are the numbered color slots that terminals use, and the 16 here cover the eight basic colors plus their bright variants.
- **`catppuccin`.** An upstream translation layer. Catppuccin is a popular theme project with well-known token names like `crust`, `mantle`, `surface0`, and `subtext0`. Neovim plugins (like Catppuccin) expect those specific names. This maps them cleanly to Flint semantic roles, so the plugins work without extra configuration.
- **`alpha`.** Declarative opacity rules in `[base_token, alpha_float]` form, like `border_70: [accent, 0.7]`. Alpha is how transparent a color is, on a scale from 0 (fully transparent) to 1 (fully opaque). Declarative here means the rules are data, not code.
- **`lut_palette`.** Lists of color anchors (`balanced`, `cool`, `warm`) that `lutgen`, the wallpaper recolor tool, uses for wallpaper remapping.
- **`base16`.** An upstream translation layer mapping semantic roles to the standard `base00` through `base0F` (plus `base16` through `base23`) scheme slots, resolved and exported like the Catppuccin layer.
- **`hue_budget`.** The hue-budget validator's data. It holds the declared hue families (anchors plus tolerance), the neutral saturation ceiling, the near-black and near-white exemptions, and the exact-token exemptions.
- **`contrast_checks`.** The contrast validator's floors, as data rows of `[fg_role, bg_role, min_ratio]`. Adding a check for a new role is a one-line edit here, not a code change.
- **`distinctness_checks`.** Adjacent-state rules as `[role_a, role_b, min_contrast, min_delta_e, context]` rows, covering pairs like hover versus focused and active versus inactive border.
- **`desktop`.** Global font names, sizes, cursor themes, and Qt style preferences.

### The `dark.yaml` and `light.yaml` files

These contain the actual hex values (`raw`), GTK theme names (`appearance`), upstream Catppuccin flavors (`mocha` versus `latte`), `semantic_overrides`, and the `qt_bevel` ladder.

A flavor is the Catppuccin term for a complete color scheme. GTK is the widget toolkit that many Linux apps use. `semantic_overrides` is the per-variant list of roles that point somewhere different from the shared defaults. `qt_bevel` is the five-step Qt button ladder, declared as raw tokens from lightest to darkest instead of hand-picked hexes. Qt is the toolkit many desktop apps are built on. The design invariants section explains the ladder in detail.

## The accent

Every variant carries exactly one accent, expressed through the semantic roles (`accent`, `accent_text`, `accent_bright`, `accent_strong`, `selection`, and `on_selection`) instead of swappable bundles. An accent is not a single color. Pointing `accent` at one raw token breaks selection contrast and fails in the light variant, so each accent is really three cooperating roles:

1. **Foreground text and icons.** Bright and readable against the base background, at 4.5:1 or more.
2. **UI highlight.** Distinct for links, focus outlines, and interactive highlights.
3. **Selection surface.** A tint with enough depth to keep the selection text readable, because `on_selection` against `selection` must reach 4.5:1. Flint uses a neutral grey-blue with near-white text. Sand uses the deep blue with the cream background as the text color.

Window borders follow the Sway white invariant instead of the accent, the Sway convention that the focused border takes the theme's most legible neutral color. The `window_focused_border` role is the theme's `text` color in both variants, light grey `#eae7e3` in Flint (the lit side of the ramp) and dark `#282522` in Sand (the dark side), so focus is the theme's most legible neutral. Blue was tested and rejected for this job, because the accent's hue matches the cool-grey inactive borders and therefore has neither luminance nor hue separation. The `focus_border` role stays the neutral `overlay_strong` grey, and the accent only appears in text, search matches, and interactive highlights.

Both variants carry the same blue accent, one hue system at two lightness extremes. Flint uses a mid blue (`accent_blue`) with a bright text variant, and Sand uses a deep blue so text keeps its contrast against the cream background.

Both ramps are warm. Sand's cream neutrals and Flint's warm dark greys share the same hue family, which sits between 33 and 39 degrees. In Flint the warmth runs the whole way down the ramp. The deep background steps carry the same family hue, so the darkest shade is a warm near-black instead of a neutral one, and no surface sits on a cold base. Chroma stays low at every step, so the warmth reads as a cast rather than a tint. The warmth does not live in the accent.

The accent roles (`accent`, `accent_strong`, and `accent_bright`) are shared defaults. Only `accent_text` needs an override, because the bright blue fails contrast on cream, and the override lives in the light variant.

## Design invariants

The palette values encode a few deliberate rules. The validator enforces the ones that can be measured. The rest are written down here so a future edit does not break them by accident.

### Terminology

The rules are full of specialist terms, so this section explains them in plain English. Each entry names the term, then says what it means and why it matters.

#### How colors are measured

- **Contrast ratio.** How readable one color is on top of another. It is a number like 3.0:1 or 4.5:1. A ratio of 1:1 means the two colors are identical, and 21:1 is black on white, the maximum-contrast pairing. The Web Content Accessibility Guidelines (WCAG) set the floors most designs follow: 4.5:1 for normal text, 3:1 for large text and UI elements like borders and buttons, and 7:1 for the enhanced accessibility level. In this palette, the validator treats those ratios as hard floors. If a pair of colors falls below its floor, the build aborts.
- **ΔE.** How different two colors actually look to a human eye. It is not raw red-green-blue (RGB) distance, because two colors can be far apart in RGB math while looking almost identical to a person. A ΔE of about 2.3 is the just-noticeable difference, and a ΔE of about 10 means the colors are clearly different. The validator uses ΔE to catch the classic failure where two "different" slots silently become the same color.
- **JND.** Short for just-noticeable difference, the ΔE threshold of about 2.3 from the previous item. When a color step sits below it, the eye cannot tell the step is there, so the separation is lost. Whenever the palette separates two colors on purpose, the gap needs to clear the JND.

#### How colors behave on screen

- **Wash and hover tint.** A wash, or hover tint, is a barely-there background tint, roughly 1:1 contrast with the base color. On its own it looks like nothing happened, which is by design. The rule that comes out of this is simple. Every hover style must also flip a border or text color in the same transition, or the hover reads as nothing at all.
- **Bevel ladder.** Qt paints buttons as a band of five shades running from light to dark. If two of those steps are near-identical, the button looks flat. These steps stay subtle, usually in the ΔE 3 to 5 range, with two deliberate exceptions. In Flint the step from `surface_0` to `bg` is a full 14.0 ΔE, because `bg` is the desktop root and `surface_0` is the first panel shade, and the panel needs a clear step away from the root. In Sand the two darkest steps, from `surface_1` to `bg_deep` and from `bg_deep` to `surface_2`, sit at 2.9 ΔE, because the cream ramp's four surface shades sit close together, and Qt uses the two darkest shades only for subtle edges. Each variant declares its ladder once as `qt_bevel` (raw tokens, lightest to darkest), and the build derives the `qt_light`, `qt_midlight`, `qt_button`, `qt_mid`, and `qt_dark` roles from it. It enforces a strictly monotonic ramp, and any two adjacent steps that fall below 1.05:1 contrast and below ΔE 4.0 at the same time are rejected as indistinguishable. The ladder is a contiguous slice of the neutral ramp, so it cannot drift out of the ramp.
- **Floor ceiling.** A floor ceiling is a color that is locked to a minimum contrast even when a "nicer" value would dip below it. Faint text must stay readable. In the dark variant, the surface ladder physically cannot carry 4.0:1 on `surface_2`, so `text_muted` on `surface_2` is floored at 3.0:1, which is the realistic limit. `overlay_strong` on the background gets the same floor.
- **Two brights in the light variant.** The word _bright_ means two different things in Sand, the light variant. The ANSI `bright_*` slots are darker than their normal counterparts, because bright text must stay readable on the cream background. The accent and error `*_bright` colors are lighter, because they are hover tints meant to stand out against the base. Same word, opposite directions, both deliberate.
- **Swaylock slices invert per variant.** The swaylock ring hosts the keystroke, backspace, and caps lock arcs. In Flint the ring is mid-grey and the arcs are light (`ansi_white`, `yellow_bright`, and `error_bright`). In Sand the ring is light (`surface_2`) and the arcs are the dark chromatic tokens (`text`, `yellow`, and `error`). A light-variant slice must be a dark color, because every light-variant chromatic token is dark by design. Pointing them at `overlay_strong` produced 1.35:1 arcs that were invisible.

#### What the colors mean

- **One gold hue.** `caution`, `warning`, and `yellow` are deliberately the same amber. That means syntax yellow in the editor, UI warnings, and the caution meter in btop all read as one color across the desktop. The three names are vocabulary, not three different colors. Keeping them identical is what makes warnings recognizable everywhere.
- **Hue is reserved for outcomes.** Idle things stay neutral, and only states that mean something get color. The swaylock ring stays grey while it is verifying, and mako notification cards keep the base background in every urgency. Color appears only for progress and failure, never for "everything is fine". Like the swaylock text that turns red only when the password is wrong, a mako card changes its text, border, and progress colors instead of repainting its surface. Chroma marks the failure state, never idle or in-progress.
- **Accent knob.** `accent` and `accent_strong` move together per variant, blue in both Flint and Sand, so links and highlights stay in agreement. `focus_border` and `window_focused_border` are deliberately split off from the accent. The `window_focused_border` role uses the `text` color, light grey in Flint and dark in Sand, the two ends of the same neutral ramp, while the `focus_border` role stays the neutral `overlay_strong` grey. Window borders stay readable against any wallpaper, while the accent lives in text, search matches, and interactive highlights.
- **`fastfetch_key` stays accent-independent.** The fastfetch logo is fixed to the Catppuccin `peach` token, so the key color must not follow the accent hue. In Flint the key is the bright blue. In Sand it is the deep blue, because the bright blue fails contrast on cream.
- **Terminal blue and UI blue are separate tokens.** In Flint, `ansi_blue` is the bright syntax blue (`#68a0ca`) and `accent_blue` is the muted UI blue (`#5a8bb0`). The terminal keeps the brighter one, because syntax highlights need the extra brightness against the dark background, and the UI accent stays muted, because it also paints fills, borders, and hover tints. One Dark does the same, with its bright syntax blue and its more saturated UI accent. In Sand the two share one token, because the cream background cannot host two different blues at the same lightness. The pair is context-separated, so the two blues do not appear together, and the split only exists in Flint.

#### Intentional lookalikes

- **`raw_aliases` versus `raw_near_aliases`.** `raw_aliases` are groups of names that must all point at the same hex value. For example, `ansi_green` and `success` are aliases of each other. The build warns if a group drifts apart. `raw_near_aliases` are pairs that are almost identical, which is fine because they are context-separated. Do not "fix" one without checking the other.
- **Context-separated.** Two colors are context-separated when they are similar but never appear in the same place, so the similarity does not matter. Terminal text and button fill are a classic example.
- **Accepted near-collisions.** `ansi_bright_red` and `error_deep` sit within ΔE 5.8 of each other. That is accepted, because the two are context-separated. One is terminal text, and the other is a button fill. Keep the gap when editing either side.

#### Search highlight ladder

Search prominence comes from depth of blue, never brightness. The same three-step structure holds in both variants:

1. **Line highlight** stays neutral (`surface0`) with no hue.
2. **Other matches** (`search_bg`) are the lighter sibling in the accent-blue family, with whichever text contrast wins.
3. **Current match** (`inc_search_bg`) is the deepest, most saturated blue of the ladder, with light text.

Do not push a search fill toward the white-blue range. Colors in that range look flashy, and they stop following the depth-of-blue structure. In Flint the ladder is `#7bb3dc` for other matches over `#5a8bb0` for the current match. In Sand it is `#4178a3` over `#225882`. The zathura `highlight-active` color follows `search_bg` at 80% alpha (`search_80`) and must track any change to step 2.

## What the build script derives

When `build_palette_data.py` runs, it derives multiple ready-to-use formats for every token, so templates do not have to reformat values by hand.

### Solid colors

The `.flint.resolved.<role>` and `.flint.raw.<token>` paths expose the solid forms:

- `.hex` is `#282828`, the standard six-digit form.
- `.bare` is `282828`, without the leading hash. The foot terminal emulator and Qt5ct, the Qt style configuration tool, use it.
- `.triple` is `40 40 40`, space-separated RGB. Zellij KDL needs it.
- `.bare_ff` is `282828ff`, with the alpha channel included. Fuzzel and swaylock use it.

### Alpha tokens

Alpha tokens represent transparent overlays. The derived `.hex` and `.bare` forms are 8-digit hex, like `#5a8bb0b2`, for apps that parse alpha such as swaylock and zathura. The `.rgba` form is a Cascading Style Sheets (CSS) `rgba(r, g, b, a)` string for waybar.

## Contrast checks

`flint_palette.py` has a built-in contrast validator that runs every time you build the palette data. The floors themselves live as data in `shared.yaml` (`contrast_checks` for paired contrast floors, `distinctness_checks` for adjacent-state rules), so adding a rule for a new role is a data edit. The validator runs WCAG relative luminance math, a measure of how bright a color looks to the eye, across every variant. It enforces these floors:

- Primary text on background must be at least 4.5:1 (WCAG AA).
- Secondary and muted text on surfaces must meet at least 4.0:1 to 4.5:1.
- Interactive borders and status highlights must meet at least 3.0:1.
- Selection text, meaning `on_selection` against `selection`, must meet at least 4.5:1.
- ANSI text must maintain at least 4.5:1 against the terminal background, and bright variants must have a measurable visual distinction from normal variants (1.05:1 or more).
- LUT anchor palettes must contain at least 12 anchors, and any two anchors inside one list must stay at least ΔE 3.0 apart, just above the just-noticeable difference, so `lutgen` does not produce visible color banding on complex wallpapers. The floor is data in `lut_min_anchor_delta_e`, and the build rejects lists that contain near-identical anchors.

The hue-budget validator guards the neutrality thesis in code. Every raw token must be near-neutral (saturation at or below 25%, which covers One Dark's neutral cast), near-black or near-white, or fall within 10 degrees of one of the seven declared hue families (One Dark's red, orange, yellow, green, cyan, blue, and purple). The `diff_*` washes and `warning_tint` are exempt, because they are intentional low-contrast tints. Any token that drifts outside the budget aborts the build.

If any pair fails to meet its contrast floor, the build script prints the failures and aborts before you can apply broken colors.

## Template usage

The export contains both variants. `flint.dark` and `flint.light` hold the full per-variant data, so apps that render both variants can be configured for both at once. The template for the foot terminal emulator, for example, renders `[colors-dark]` and `[colors-light]` side by side. The top-level sections (`resolved`, `alpha`, `ansi_resolved`, `catppuccin_resolved`, and `base16_resolved`) alias the active variant, so most templates keep reading `.flint.resolved` and automatically follow `make dark` and `make light`.

Any file ending in `.tmpl` can read values directly from `.flint`. The swaylock template shows the pattern, pulling roles from the active variant alias and writing them into the config:

```ini
# Pattern from home/dot_config/swaylock/config.tmpl
#{{ $c := .flint.resolved }}

ring-color={{ $c.swaylock_ring.bare_ff }}
inside-color={{ $c.background.bare_ff }}
text-color={{ $c.text.bare_ff }}
```

To switch variants, see [Switch variants](theming.md#switch-variants) in the theming section.

## Summary

Here is the whole system in a few sentences. The palette files in `palettes/flint/` are the single source of truth. `shared.yaml` holds everything variant-independent, including the core semantic roles, app namespaces, the contrast and distinctness rule tables, and desktop metrics. `dark.yaml` and `light.yaml` hold the raw hex values, overrides, and the Qt bevel ladder. The build script validates the design invariants, derives every format a template could need, and exports both variants, with aliases for the active variant, into `.chezmoidata.yaml`. At apply time, templates pull their colors from there. And when you edit a palette, the contrast validator catches mistakes before you can apply broken colors.
