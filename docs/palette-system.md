# Palette system

Updating colors across dozens of configuration files was tedious. The _palette_
uses a single source of truth for the entire desktop. The palette is the set of
files that defines every color in this setup.

This section explains how the palette system works. It covers how the files are
organized, what the build script derives from them, why the colors stay
readable, and how templates pull values out at apply time. It is written for
people who are new to this kind of setup, so every term is defined the first
time it appears.

## Overview

The palette files live in `palettes/flint/`:

```
palettes/flint/
├── shared.yaml    # Functional roles, ANSI slots, Catppuccin aliases, app namespaces, alpha rules, contrast rules, desktop metrics
├── dark.yaml      # Flint raw hex values, dark-specific overrides, the Qt bevel ladder
└── light.yaml     # Sand raw hex values, light-specific overrides, the Qt bevel ladder
```

Before touching the files, learn two terms:

- A _raw token_ is a named color value, the actual hex like `#303030`.
- A _semantic role_ is a named job a color does, like `background` or
  `focus_border`. Roles point at tokens, and the same role can point at
  different tokens in different variants.

`scripts/build_palette_data.py` validates the palette, computes all necessary
formats and alpha blends, and writes `.chezmoidata.yaml` into `home/`. When you
run `chezmoi apply`, chezmoi reads that file and injects the colors into any
`.tmpl` configuration.

Changing a color takes the same steps every time:

1. Edit a palette file.
2. Run the build script.
3. Apply with chezmoi.

The sections that follow cover those steps, from the files to the derived data
to the checks that catch mistakes.

## How the files are structured

### The shared configuration file

The `shared.yaml` file defines everything that is not tied to a specific color
variant:

- **`semantic`.** Functional names that map roles to raw tokens, like
  `background: bg`, `accent_text: accent_blue_bright`, and
  `focus_border: overlay_strong`. Your configs mostly consume these semantic
  roles.
- **`apps`.** App-specific roles, namespaced per application. Each entry
  `apps.<app>.<key>` becomes the flat role `<app>_<key>` at load time, so
  `apps.qt.base` turns into the role `qt_base`. This keeps new applications from
  polluting the core role vocabulary.
- **`ansi`.** The standard 16-color terminal slots (`black`, `red`, `green`, and
  the rest). ANSI colors are the numbered color slots that terminals use, and
  the 16 here cover the eight basic colors plus their bright variants.
- **`catppuccin`.** A bridge to the token names another theme project uses.
  Catppuccin is a popular theme project with well-known token names like
  `crust`, `mantle`, `surface0`, and `subtext0`. Neovim plugins (like
  Catppuccin) expect those specific names. This maps them cleanly to the Flint
  theme's semantic roles, so the plugins work without extra configuration.
- **`alpha`.** Declarative opacity rules in `[base_token, alpha_float]` form,
  like `border_70: [accent, 0.7]`. Alpha is how transparent a color is, on a
  scale from 0 (fully transparent) to 1 (fully opaque). Declarative here means
  the rules are data, not code.
- **`lut_palette`.** Lists of color anchors (`balanced`, `cool`, `warm`) that
  `lutgen`, the wallpaper recolor tool, uses for wallpaper remapping.
- **`contrast_checks`.** Selected Web Content Accessibility Guidelines (WCAG)
  2.2 AA contrast pairs (`https://www.w3.org/TR/WCAG22/`), as data rows of
  `[fg_role, bg_role, min_ratio]`. Each row maps to 1.4.3 Contrast (Minimum) at
  4.5:1 or 1.4.11 Non-text Contrast at 3:1. Adding a check for a new role is a
  one-line edit here, not a code change. These rows are a subset of AA, not a
  conformance claim.
- **`desktop`.** Global font names, sizes, cursor themes, and Qt style
  preferences.

### The dark and light configuration files

The `dark.yaml` and `light.yaml` files contain the actual hex values (`raw`),
_GIMP Toolkit_ (_GTK_) theme names (`appearance`), upstream Catppuccin flavors
(`mocha` versus `latte`), `semantic_overrides`, and the `qt_bevel` ladder.

A flavor is the Catppuccin term for a complete color scheme. GTK is the widget
toolkit that many Linux apps use. `semantic_overrides` is the per-variant list
of roles that point somewhere different from the shared defaults. `qt_bevel` is
the five-step Qt button ladder, declared as raw tokens from lightest to darkest
instead of hand-picked hexes. Qt is the toolkit many desktop apps are built on.
The design invariants section explains the ladder in detail.

## The accent

Every variant carries exactly one accent. It is expressed through the semantic
roles (`accent`, `accent_text`, `accent_bright`, `accent_strong`, `selection`,
and `on_selection`), not through swappable bundles. An accent is not a single
color. Pointing `accent` at one raw token breaks selection contrast and fails in
the light variant. Each accent is really three cooperating roles:

1. **Foreground text and icons.** Bright and readable against the base
   background, at 4.5:1 or more
2. **UI highlight.** Distinct for links, focus outlines, and interactive
   highlights
3. **Selection surface.** A tint with enough depth to keep the selection text
   readable, because `on_selection` against `selection` must reach 4.5:1. Flint
   uses a blue-tinted steel with near-white text. Sand uses the deep blue with
   the light background as the text color.

Window borders follow the focus gray instead of the accent or plain white. In
Flint the focused frame takes the neutral `overlay_strong` grey, which clears
3:1 against both the background and the inactive frame, so windows separate at
seams without a glowing outline. Sand keeps the near-black `text` frame, which
reads calm on light chrome. Dimming already pushes unfocused windows back, so a
near-white border on dark would only shout what the dimming already says. Blue
was tested and rejected for this job, because blurple fails seam separation
against the inactive frame and bright blue is the most luminous token in the
palette. The `focus_border` role is the same grey, so Sway windows and pane
frames signal focus in one voice, and the accent only appears in text, search
matches, and interactive highlights. Row and menu highlights use `text` rather
than `text_max` for the same reason. Near-white stays reserved for text riding
on dark fills, where it earns its contrast.

Both variants share one hue system at two lightness extremes. Syntax hues follow
One Dark Pro (`#E06C75` / `#98C379` / `#E5C07B` / `#61AFEF` / `#C678DD` /
`#56B6C2` / `#D19A66`), verified against the upstream `OneDark-Pro.json` and
`onedark.nvim` palettes. UI fills follow Discord (`#5865F2` blurple for accent
fills, `#1E1F22` / `#2B2D31` / `#313338` neutrals, `#DBDEE1` text). Light hues
follow `onedark.nvim` light (`#E45649` / `#50A14F` / `#986801` / `#4078F2` /
`#A626A4` / `#0184BC` / `#C18401`), darkened at the same hue until 4.5:1 passes
on `#F2F3F5`.

Both ramps are sterile cool-grays in the Discord and Chrome style, with
chromatic color reserved for meaningful states. Dark `bg` is `#1E1F22` with
`surface_0` as the first panel step. Light `bg` is `#F2F3F5` with the
`bg_subtle` wash lighter than the root. The working surfaces step away from `bg`
so the bevel keeps legible steps. Night warmth comes from `wlsunset`, not from
the hexes, so the palette stays neutral on purpose.

Match means visual alignment, not just AA. Hues stay locked to the references
above, neutrals stay under 15% saturation, chromatics stay above 22% with a
clear gap, and lightness moves instead of desaturation whenever contrast needs
work. Dark One Dark hues pass 4.5 untouched on `#1E1F22` except blurple, which
is graphics-only. Light hues are the same hues darkened until 4.5 passes.

The accent roles (`accent`, `accent_strong`, and `accent_bright`) are shared
defaults. Only `accent_text` needs an override, because the bright blue fails
contrast on the light background, and the override lives in the light variant.

## Design invariants

The palette values encode a few deliberate rules. The validator enforces the
ones that can be measured. The rest are written down here so a future edit does
not break them by accident.

### Terminology

The rules are full of specialist terms, so this section explains them in plain
English. Each entry names the term, then says what it means and why it matters.

#### How colors are measured

- **Contrast ratio.** How readable one color is on top of another. It is a
  number like 3.0:1 or 4.5:1. A ratio of 1:1 means the two colors are identical,
  and 21:1 is black on white, the maximum-contrast pairing. The Web Content
  Accessibility Guidelines (WCAG) 2.2 (`https://www.w3.org/TR/WCAG22/`) set the
  floors this palette follows for its listed pairs: 4.5:1 for normal text under
  1.4.3 Contrast (Minimum) (`https://www.w3.org/TR/WCAG22/#contrast-minimum`),
  3:1 for large text under 1.4.3, and 3:1 for UI boundaries and meaningful
  graphics under 1.4.11 Non-text Contrast
  (`https://www.w3.org/TR/WCAG22/#non-text-contrast`). All body-text roles in
  this palette are normal size, so 4.5:1 applies and the large-text 3:1
  concession is unused. The 7:1 level belongs to AAA enhanced contrast, not AA,
  and this palette does not enforce it. If a listed pair of colors falls below
  its AA floor, the build aborts. Listed pairs passing is not a WCAG AA
  conformance claim, which applies to full pages and processes and needs 1.4.1,
  2.4.7, 2.4.11, and the other AA criteria too.

#### How colors behave on screen

- **Wash and hover tint.** A wash, or hover tint, is a barely-there background
  tint, roughly 1:1 contrast with the base color. On its own it looks like
  nothing happened, which is by design. The rule that comes out of this is
  simple. Every hover style must also flip a border or text color in the same
  transition, or the hover reads as nothing at all.
- **Bevel ladder.** Qt paints buttons as a band of five shades running from
  light to dark. Each variant declares its ladder once as `qt_bevel` (raw
  tokens, lightest to darkest), and the build derives the `qt_light`,
  `qt_midlight`, `qt_button`, `qt_mid`, and `qt_dark` roles from it. Order is
  not a WCAG requirement and carries no contrast floor.
- **Muted text stays readable.** Faint text must stay readable. Every muted-text
  pair that renders body text is held to 4.5:1, including `text_muted` on
  `surface_2` and `overlay_dim` captions on the background, and cyan text on
  `surface_1`. If a future template puts body text somewhere new, add the pair
  instead of lowering a floor. `focus_border` on the background is a boundary
  and stays at 3:1.
- **Two brights in the light variant.** The word _bright_ means two different
  things in Sand, the light variant. The ANSI `bright_*` slots are darker than
  their normal counterparts, because bright text must stay readable on the light
  background. The accent and error `*_bright` colors are lighter, because they
  are hover tints meant to stand out against the base. Same word, opposite
  directions, both deliberate.
- **Swaylock slices invert per variant.** The swaylock ring hosts the keystroke,
  backspace, and caps lock arcs. In Flint the ring is the dark surface shade and
  the arcs are light (`ansi_white`, `yellow_bright`, and `error_bright`). In
  Sand the ring is the lightest wash and the arcs are the dark tokens (`text`,
  `yellow`, and `error`). A light-variant slice must be a dark color, because
  every light-variant chromatic token is dark by design. Each arc is held to 3:1
  against both the ring and the inside fill (the background) as UI graphics
  under 1.4.11.
- **Focus never sits on selection.** No mid-gray passes the background,
  selection, and surface adjacencies at 3:1 all at once, so instead of a color
  that fails somewhere, focus rings are scoped to pane frames and backgrounds
  and never drawn on selection fills. Lazygit draws the active border on the
  pane frame, waybar only defines the token without painting it over selected
  rows, and fuzzel borders use the window color. If a template starts drawing
  focus on a selection fill, add the pair instead of shipping it unchecked.
- **Selection fills are text-backed by house contract, not by WCAG exemption.**
  Selection and diff washes read as nothing on their own against the background,
  which is by design. WCAG has no text-backed exemption, so their contract is
  that text always rides on top: every consumer remaps the foreground
  (`terminal_selection_fg` in foot, `on_selection` in zellij, btop, zathura, and
  nvim, `on_accent` on `diff_text`). The dark delete wash stays shallow on
  purpose to protect red-text contrast, and deletion always pairs with a
  non-color cue, gitsigns gutter signs and lazygit +/- markers, so the wash is
  never the only signal.

#### What the colors mean

- **One gold hue, one orange hue.** `caution`, `warning`, and `yellow` are
  deliberately the same amber. That means syntax yellow in the editor, UI
  warnings, and the caution meter in btop all read as one color across the
  desktop. The three names are vocabulary, not three different colors. Keeping
  them identical is what makes warnings recognizable everywhere. `peach` is the
  separate orange hue for commit hashes and constants, distinct from the gold in
  both variants, so the two never collide. State-vs-state pairs like error
  against warning have no WCAG ratio floor. Telling them apart comes from hue
  plus the non-color cues above, never color alone.
- **Hue is reserved for outcomes.** Idle things stay neutral, and only states
  that mean something get color. The swaylock ring stays grey while it is
  verifying, and dunst notification cards keep the base background in every
  urgency. Color appears only for progress and failure, never for "everything is
  fine". Like the swaylock text that turns red only when the password is wrong,
  a dunst card changes its text, border, and progress colors instead of
  repainting its surface. Chroma marks the failure state, never idle or
  in-progress.
- **Accent knob.** `accent` and `accent_strong` move together per variant, blue
  in both Flint and Sand, so links and highlights stay in agreement.
  `focus_border` and `window_focused_border` are deliberately split off from the
  accent. In Flint the window frame uses the neutral `overlay_strong` grey, the
  same voice as pane focus borders. In Sand it keeps the near-black `text`
  color, which reads calm on light chrome. Window borders stay readable against
  any wallpaper, while the accent lives in text, search matches, and interactive
  highlights.
- **`fastfetch_key` stays accent-independent.** The fastfetch logo is fixed to
  the Catppuccin `peach` token, so the key color must not follow the accent hue.
  In Flint the key is the bright blue. In Sand it is the deep blue, because the
  bright blue fails contrast on the light background.
- **Terminal blue and UI blue are separate tokens.** In Flint, `ansi_blue` is
  the dusty syntax blue and `accent_blue` is the deeper UI blue. The terminal
  keeps the brighter one, because syntax highlights need the extra brightness
  against the dark background. The UI accent stays deeper, because it also
  paints search fills that must carry light text at 4.5:1. In Sand the two stay
  separate as well, with `ansi_blue` as the dark terminal blue and `accent_blue`
  as the deep fill blue.

#### Search highlight ladder

Search prominence comes from depth of blue, never brightness. The same
three-step structure holds in both variants:

1. **Line highlight** stays neutral (`surface0`) with no hue.
2. **Other matches** (`search_bg`) are the lighter sibling in the accent-blue
   family, with whichever text contrast wins.
3. **Current match** (`inc_search_bg`) is the deepest, most saturated blue of
   the ladder, with light text.

Do not push a search fill toward the white-blue range. Colors in that range look
flashy, and they stop following the depth-of-blue structure. The zathura
`highlight-active` color follows `search_bg` at 80% alpha (`search_80`) and must
track any change to step 2.

## What the build script derives

When `build_palette_data.py` runs, it derives multiple ready-to-use formats for
every token, so templates do not have to reformat values by hand.

### Solid colors

The `.flint.resolved.<role>` and `.flint.raw.<token>` paths expose the solid
forms:

- `.hex` is `#282828`, the standard six-digit form.
- `.bare` is `282828`, without the leading hash. The foot terminal emulator and
  Qt5ct, the Qt style configuration tool, use it.
- `.triple` is `40 40 40`, space-separated RGB. Zellij KDL needs it.
- `.bare_ff` is `282828ff`, with the alpha channel included. Fuzzel and swaylock
  use it.

### Alpha tokens

Alpha tokens represent transparent overlays. The derived `.hex` and `.bare`
forms are 8-digit hex, like `#3281EAb2`, for apps that parse alpha such as
swaylock and zathura. The `.rgba` form is a _Cascading Style Sheets_ (_CSS_)
`rgba(r, g, b, a)` string for waybar.

## Contrast checks

`flint_palette.py` has a built-in validator that runs every time you build the
palette data. The floors themselves live as data in `shared.yaml`
(`contrast_checks`), so adding a rule for a new role is a data edit. The
validator runs WCAG 2.2 relative luminance math, a measure of how bright a color
looks to the eye, across every variant. It enforces selected WCAG 2.2 AA
contrast pairs only, 1.4.3 at 4.5:1 and 1.4.11 at 3:1, for the rows in
`contrast_checks` plus ANSI body text on the terminal background. That is a
subset of AA, not AA conformance:

- Body text on its background must be at least 4.5:1 under 1.4.3. That covers
  the listed primary, secondary, and muted text, selection text, notification
  cards, Qt surfaces, search matches, and accent text used as body text. All
  text roles are normal size, so the large-text 3:1 concession does not apply. A
  new template pair without a new row is unchecked, so add the row.
- UI boundaries and meaningful graphics must be at least 3:1 against the listed
  adjacent color under 1.4.11. That covers the focus border, swaylock arcs
  against the ring and inside fill, and status strokes that never render body
  text. Inactive borders are exempt as inactive components and carry no floor.
  Only the listed adjacency is checked, not every adjacent color, and focus on
  selection fills is out of scope by the focus contract below.
- ANSI body text must maintain at least 4.5:1 against the terminal background.
  Surfaces are not terminal backgrounds, so they carry no blanket ANSI floor.
  Excluded ANSI tokens, alpha composites, bevels, LUTs, and wallpapers are
  unchecked by design.

If any listed AA pair fails to meet its floor, the build script prints the
failures and aborts before you can apply broken colors. Passing pairs do not
make a desktop WCAG AA conformant. Focus 3:1 here is 1.4.11 adjacent-color only
and does not meet 2.4.13 AAA focus appearance, which also needs area and a
focused-versus-unfocused change.

## Template usage

The export contains both variants. `flint.dark` and `flint.light` hold the full
per-variant data, so apps that render both variants can be configured for both
at once. The template for the foot terminal emulator, for example, renders
`[colors-dark]` and `[colors-light]` side by side. The top-level sections
(`resolved`, `alpha`, `ansi_resolved`, and `catppuccin_resolved`) alias the
active variant, so most templates keep reading `.flint.resolved` and
automatically follow `make dark` and `make light`.

Any file ending in `.tmpl` can read values directly from `.flint`. The swaylock
template shows the pattern, pulling roles from the active variant alias and
writing them into the config:

```ini
# Pattern from home/dot_config/swaylock/config.tmpl
#{{ $c := .flint.resolved }}

ring-color={{ $c.swaylock_ring.bare_ff }}
inside-color={{ $c.background.bare_ff }}
text-color={{ $c.text.bare_ff }}
```

For more information about switching variants, see
[Switch variants](theming.md#switch-variants) in the theming section.
