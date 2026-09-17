# Color scheme: One Dark on Neutral — design reference

The single source of truth for every color this desktop uses. The locked hexes
below are seeds: the supporting tints derive from them via the specs in the
tints table (`meta/palette.py` computes each as
`oklch(anchor L, base C × k, base H)`), and `meta/palette.py check` verifies
that every hex in every app file traces to this doc. The fix is the locked ramp
plus derivation specs — machine-checked, hand-readable. A color change
propagates seed-first: edit a hex or spec here, run `meta/palette.py`, paste the
hexes, re-run for the check.

## Rationale

- One temperature: pure neutral grays for all grounds. One Dark Pro classic
  (`refs/onedark-pro/src/themes/themeData.ts`, `textColors.classic`) supplies
  every chromatic hue angle; chroma is boosted ×1.5 at constant lightness and
  hue. Nothing else.
- One accent: `#48AFFF`, bright `#98C3FF`. Every app's focused, selected, link,
  and cursor state uses this pair. No per-app accents, no second blue.
- Hierarchy is guaranteed by the ramp, not by per-file judgement: every tier
  below is monotonic and distinct. No two roles share a hex — the collapsed
  tiers (`subtext1 = text`, `overlay0 = overlay1`) that made the editor look
  arbitrary are what this table forbids.
- The doc is the boundary: any hex pasted into an app file must exist here.
  App-local inventions (a Discord-indigo sapphire, a lone material-red maroon)
  are how drift starts.

## Neutrals (locked ramp, dark → light)

| Hex       | Role      | Used for                                                    |
| --------- | --------- | ----------------------------------------------------------- |
| `#101010` | crust     | nvim TabLine, fold backgrounds                              |
| `#171717` | mantle    | nvim floats, pickers, Pmenu — transient chrome              |
| `#202020` | base      | editor, terminal, bar, notification, window backgrounds     |
| `#262626` | surface-0 | cursorline, alternate base, tooltip base                    |
| `#2D2D2D` | surface-1 | hover fills, buttons, menu selection, dunst normal bg       |
| `#3A3A3A` | surface-2 | borders, selections, indent guides, dunst low frame         |
| `#5A5A5A` | line      | focus borders, float borders, subtle lines                  |
| `#8A8A8A` | muted     | comments (italic), placeholders, disabled, low-urgency text |
| `#B3B3B3` | subtext   | secondary text: titles, tab labels, dimmed emphasis         |
| `#D4D4D4` | text      | primary text everywhere                                     |
| `#FFFFFF` | text-max  | hover, selected, max emphasis                               |

Crust and mantle are nvim-only by design — an editor reads more depth than a bar
— but they are part of this ramp, not local inventions. The editor may never
step outside these eleven values.

## Chromatics (One Dark Pro hues, chroma boosted ×1.5)

| Hue    | Base      | Bright    | Semantics                                         |
| ------ | --------- | --------- | ------------------------------------------------- |
| red    | `#FE4864` | `#FF7376` | error, urgent, git-deleted, specials              |
| green  | `#89C952` | `#B9EE7D` | success, git-added, strings                       |
| yellow | `#F4BC45` | `#FFD678` | warning, git-modified, types                      |
| blue   | `#48AFFF` | `#98C3FF` | **the accent**: links, cursor, focus, directories |
| purple | `#D95AFC` | `#E67FFF` | keywords, root names                              |
| cyan   | `#00BBCC` | `#3DDAEE` | enum members, secondary types                     |
| orange | `#E49137` | `#F2A256` | numbers, properties, dashboard header             |

Dropped deliberately: sapphire and maroon as hues (unused outliers), the
mauve/lavender split (purple + purple-bright covers it). Catppuccin's
`maroon`/`sapphire` slots are set to the red/blue hexes so no stock pastel
renders. Seven hues, each with exactly one bright step. No new hues without
editing this table first.

## Supporting tints (derived, on the lattice)

Specs are seeds: anchor = a ramp role, hue = a chromatic, k = chroma fraction of
that hue's base. `meta/palette.py` derives each hex as
`oklch(anchor L, base C × k, base H)` — the same scaffolding as the LUT palette,
snapped to the ramp's lightness steps and the hues' angles. Edit a spec, run
`meta/palette.py`, paste the hex; never hand-edit the Hex column. The one alpha
overlay below is not derivable and stays hand-written.

| Tint          | Anchor    | Hue    | k     | Hex                      | Used for                                |
| ------------- | --------- | ------ | ----- | ------------------------ | --------------------------------------- |
| hover         | —         | —      | —     | `rgba(255,255,255,0.08)` | bar hover fill (alpha overlay)          |
| warning-hover | surface-1 | yellow | 0.302 | `#382B11` | waybar + btop warning hover fill |
| error-hover | surface-1 | red | 0.256 | `#452123` | waybar + btop error hover fill |
| selection | surface-2 | blue | 0.179 | `#2F3C47` | btop selection, nvim Visual + Search bg |
| diff-add | surface-2 | green | 0.432 | `#2B4218` | nvim DiffAdd |
| diff-change | surface-2 | blue | 0.444 | `#183D5A` | nvim DiffChange |
| diff-delete | surface-0 | red | 0.208 | `#391C1E` | nvim DiffDelete |
| diff-text | line | blue | 0.562 | `#2D5E86` | nvim DiffText |

## Utility colors (locked, outside the ramp)

| Hex       | Used for                                             |
| --------- | ---------------------------------------------------- |
| `#000000` | shadows — always alpha-carried (`#00000080` in sway) |

## Rules

1. **Ramp integrity.** Monotonic dark → light; no two roles share a hex. Checked
   by eye against the table above.
2. **Text hierarchy.** text-max > text > subtext > muted, each visibly distinct
   on `#202020`. Titles are subtext, never text. Comments are muted, italic,
   never overlay. `meta/palette.py check` reports the contrast ratios
   (informational, never a gate).
3. **One accent pair.** Focused/selected/link/cursor states use
   `#48AFFF`/`#98C3FF` in every app. Search follows: IncSearch is accent
   (`#48AFFF` bg, base fg); Search is the selection ground (the derived
   `selection` tint, text fg). Search is never gray.
4. **Transient chrome uniformity.** Floats, pickers, and Pmenu sit on mantle,
   all of them, with one border color (`line #5A5A5A`). Preview panes may sit on
   base. No third depth.
5. **Doc boundary.** Every hex in an app file traces to this doc — enforced by
   `meta/palette.py check`, not by eye. The check reads `#hex` (8-digit alpha
   stripped) and foot-style bare `key=value` hexes; quoted bare hexes and
   `rgba()` are not read, so keep app files in one of the covered forms. When a
   color must change, change it here first, run `meta/palette.py`, paste.

## Syntax layer (One Dark Pro standard, for the nvim pass)

| Capture                       | Hex              |        |
| ----------------------------- | ---------------- | ------ |
| `@keyword`                    | `#D95AFC`        | purple |
| `@function`                   | `#48AFFF`        | blue   |
| `@string`                     | `#89C952`        | green  |
| `@number` / `@constant`       | `#E49137`        | orange |
| `@type`                       | `#F4BC45`        | yellow |
| `@variable`                   | `#D4D4D4`        | text   |
| `@variable.parameter`         | `#D4D4D4`        | text   |
| special / `@variable.builtin` | `#FE4864`        | red    |
| `@property` / members         | `#E49137`        | orange |
| enum member                   | `#00BBCC`        | cyan   |
| `@operator`                   | `#00BBCC`        | cyan   |
| `@comment`                    | `#8A8A8A` italic | muted  |

Chrome-only custom_highlights may stay, but these captures must resolve to this
table — through catppuccin's default links or explicit overrides, either is fine
as long as `:Inspect` shows the hexes above.

Kept deviations from One Dark Pro's tokenColors, deliberate: `@property` /
members stay orange (upstream splits them red/yellow/gray by language — orange
is our unified call); `@variable.builtin` stays red (upstream yellows
`self`/`this`); `@variable` stays text (upstream's declared rule is red, but its
rendered output is gray — we match the rendering); punctuation is dimmed one
step to muted (upstream keeps it at text level); warnings stay yellow
(upstream's editor warnings are orange).

## Non-goals

The one-shot generator derives tints, the LUT palette, and the drift check; the
doc stays the seed truth.

- No palette builder, no `palettes/` directory.
- No contrast-gate tooling.
- No `.tmpl` color variables.
- No GTK theme change.
