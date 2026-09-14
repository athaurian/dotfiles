# Color scheme: One Dark on Neutral — design reference

The single source of truth for every color this desktop uses. Static hex
only; each app file pastes from this doc by hand. This doc replaces the
palette tables in `color-scheme-plan.md` and exists because both prior
approaches failed in opposite ways: the generator enforced coherence but
made every change expensive; the static rebuild was cheap but collapsed
the hierarchy the generator used to guarantee. The fix is the rules
below, applied by hand — the gates are a checklist now, not tooling.

## Rationale

- One temperature: pure neutral grays for all grounds. One Dark Pro
  classic (`refs/src/themes/data/themeData.ts`, `textColors.classic`)
  supplies every chromatic hue. Nothing else.
- One accent: `#61AFEF`, bright `#98C3FF`. Every app's focused, selected,
  link, and cursor state uses this pair. No per-app accents, no second
  blue.
- Hierarchy is guaranteed by the ramp, not by per-file judgement: every
  tier below is monotonic and distinct. No two roles share a hex — the
  collapsed tiers (`subtext1 = text`, `overlay0 = overlay1`) that made
  the editor look arbitrary are what this table forbids.
- The doc is the boundary: any hex pasted into an app file must exist
  here. App-local inventions (a Discord-indigo sapphire, a lone
  material-red maroon) are how drift starts.

## Neutrals (locked ramp, dark → light)

| Hex | Role | Weight | Used for |
|---|---|---|---|
| `#101010` | crust | deepest | nvim TabLine, fold backgrounds |
| `#171717` | mantle | deep | nvim floats, pickers, Pmenu — transient chrome |
| `#202020` | base | floor | editor, terminal, bar, notification, window backgrounds |
| `#262626` | surface-0 | shallow | cursorline, alternate base, tooltip base |
| `#2D2D2D` | surface-1 | | hover fills, buttons, menu selection, dunst normal bg |
| `#3A3A3A` | surface-2 | | borders, selections, indent guides, dunst low frame |
| `#5A5A5A` | line | | focus borders, float borders, subtle lines |
| `#8A8A8A` | muted | | comments (italic), placeholders, disabled, low-urgency text |
| `#B3B3B3` | subtext | | secondary text: titles, tab labels, dimmed emphasis |
| `#D4D4D4` | text | | primary text everywhere |
| `#FFFFFF` | text-max | | hover, selected, max emphasis |

Crust and mantle are nvim-only by design — an editor reads more depth
than a bar — but they are part of this ramp, not local inventions. The
editor may never step outside these eleven values.

## Chromatics (One Dark Pro classic)

| Hue | Base | Bright | Semantics |
|---|---|---|---|
| red | `#E06C75` | `#F08080` | error, urgent, git-deleted, specials |
| green | `#98C379` | `#C4E8A0` | success, git-added, strings |
| yellow | `#E5C07B` | `#F5D898` | warning, git-modified, types |
| blue | `#61AFEF` | `#98C3FF` | **the accent**: links, cursor, focus, directories |
| purple | `#C678DD` | `#D890EA` | keywords, root names |
| cyan | `#56B6C2` | `#7DD3E0` | enum members, secondary types |
| orange | `#D19A66` | `#DFAA7B` | numbers, properties, dashboard header |

Dropped deliberately: sapphire `#5865F2` and maroon `#C62828` (unused
outliers), the mauve/lavender split (purple + purple-bright covers it).
Seven hues, each with exactly one bright step. No new hues without
editing this table first.

## Supporting tints

| Hex | Used for |
|---|---|
| `rgba(255,255,255,0.08)` | bar hover fill |
| `#33291A` | bar warning hover fill |
| `#3A2224` | bar error hover fill |
| `#3A3F4B` | selection ground (foot selection, nvim Visual) |
| `#2B4632` `#1F3A52` `#332024` `#2C5372` | nvim diff add/change/delete/text |

## Rules the gates used to enforce

1. **Ramp integrity.** Monotonic dark → light; no two roles share a hex.
   Checked by eye against the table above.
2. **Text hierarchy.** text-max > text > subtext > muted, each visibly
   distinct on `#202020`. Titles are subtext, never text. Comments are
   muted, italic, never overlay.
3. **One accent pair.** Focused/selected/link/cursor states use
   `#61AFEF`/`#98C3FF` in every app. Search follows: IncSearch is accent
   (`#61AFEF` bg, base fg); Search is the selection ground (`#3A3F4B`
   bg, text fg). Search is never gray.
4. **Transient chrome uniformity.** Floats, pickers, and Pmenu sit on
   mantle, all of them, with one border color (`line #5A5A5A`). Preview
   panes may sit on base. No third depth.
5. **Doc boundary.** Every hex in an app file traces to this doc. When a
   color must change, change it here first, then paste.

## Syntax layer (One Dark Pro standard, for the nvim pass)

| Capture | Hex | |
|---|---|---|
| `@keyword` | `#C678DD` | purple |
| `@function` | `#61AFEF` | blue |
| `@string` | `#98C379` | green |
| `@number` / `@constant` | `#D19A66` | orange |
| `@type` | `#E5C07B` | yellow |
| `@variable` | `#D4D4D4` | text |
| special / `@variable.builtin` | `#E06C75` | red |
| `@property` / members | `#D19A66` | orange |
| enum member | `#56B6C2` | cyan |
| `@comment` | `#8A8A8A` italic | muted |

Chrome-only custom_highlights may stay, but these captures must resolve
to this table — through catppuccin's default links or explicit overrides,
either is fine as long as `:Inspect` shows the hexes above.

## Violations to correct (from the archive audit)

1. `subtext1 = text = #D4D4D4` → titles to `#B3B3B3` (rule 2).
2. `overlay0 = overlay1 = #5A5A5A`, `overlay2 = #8A8A8A` → collapsed and
   inverted; replace with the `line` role for borders, muted for
   comments (rule 4).
3. Comment styling dropped → restore muted italic (rule 2).
4. Search on gray → accent/selection split (rule 3).
5. Three picker depths → mantle uniformly (rule 4).
6. `blue = #98C3FF` as interactive → accent is `#61AFEF`; `#98C3FF` is
   bright-state only (rule 3).
7. sapphire `#5865F2`, maroon `#C62828` declared but orphaned → delete
   (doc boundary).

## Non-goals

No palette builder, no `palettes/` directory, no contrast-gate tooling,
no `.tmpl` color variables. The doc is the generator now — a checklist
instead of a program. No wallpaper recoloring, no GTK theme change.
