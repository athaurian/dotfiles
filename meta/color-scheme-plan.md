# Color scheme plan: One Dark chromatics on neutral grounds

Goal: retire the provisional `tmp-*` palette with one locked, tasteful
scheme — Binaryify One Dark Pro chromatics (`refs/src/themes/data/`,
`textColors.classic`) on neutral, professional backgrounds (our current
ramp, which already lands on the upstream Gnome variant's nodes
`#202020` / `#2d2d2d`). Static hex pastes only: no builder, no
`palettes/` revival, no `.tmpl` color variables (house rule 2).

## Locked palette

Neutrals (unchanged hexes; `tmp-` prefix renamed to `neutral-` in the one
file that names colors, `waybar/style.css`):

| Role | Hex | Used for |
|---|---|---|
| base | `#202020` | bar, editor, terminal bg |
| mantle | `#171717` | nvim floats, Pmenu (nvim-only) |
| crust | `#101010` | nvim deepest (nvim-only) |
| surface-0 | `#262626` | cursorline, alt base (nvim-only) |
| surface-1 | `#2D2D2D` | bar hover surfaces, dunst normal bg, Qt windows |
| surface-2 | `#3A3A3A` | borders, selections |
| text | `#D4D4D4` | primary text everywhere |
| text-max | `#FFFFFF` | hover/selected text |
| text-muted | `#8A8A8A` | comments-muted, placeholders, dim |
| overlay | `#5A5A5A` | focus borders, float borders |
| hover-neutral | `rgba(255,255,255,0.08)` | bar hover fill |
| hover-warning | `#33291A` | warning hover fill |
| hover-error | `#3A2224` | error hover fill |
| selection | `#3A3F4B` | foot selection, nvim Visual (keep: tested, readable) |
| diff depths | `#2B4632` `#1F3A52` `#332024` `#2C5372` | nvim diffs (keep, from Flint v3) |

Chromatics (One Dark Pro `classic`, verified against
`refs/src/themes/data/themeData.ts`; identical to our Flint v3 set from
`50c1062:palettes/flint/dark.yaml`):

| Role | Hex | Bright | Notes |
|---|---|---|---|
| red | `#E06C75` | `#F0A0A5` | errors, urgent, git-deleted |
| green | `#98C379` | `#C4E8A0` | success, git-added |
| yellow | `#E5C07B` | `#F5D898` | warnings, git-modified |
| blue | `#61AFEF` | `#98C3FF` | accent, links, cursor, directories |
| purple | `#C678DD` | `#D890EA` | mauve role |
| cyan | `#56B6C2` | `#7DD3E0` | teal role |
| orange | `#D19A66` | `#DFAA7B` | peach role, dashboard header |

Deliberate keeps (not oversights): bright magenta `#E3A2F8` (Flint,
softer than upstream terminal `#de73ff`); error-deep `#C62828`;
sapphire `#5865F2` slot stays unused as today.

Accent decision: `accent-text #7AA2F7` → **`#61AFEF`**,
`accent-bright #9AB8FF` → **`#98C3FF`**. The periwinkle is the only
electric outlier; sky blue is calmer, already our foot cursor, and
normalizes fuzzel (`#9AB8FF` is one digit off `#98C3FF` today).

## Per-file deltas (the whole rollout)

1. `waybar/style.css`: rename `tmp-*` → `neutral-*` (mechanical),
   accent `#7aa2f7` → `#61afef`, `#9ab8ff` → `#98c3ff`. Nothing else:
   current selectors already equal history minus dead modules.
2. `sway/config`: no color change (focus `#5a5a5a`, urgent `#e06c75`
   already fit). `exec_always` applet lines stay.
3. `foot/foot.ini`: no change. Regular ANSI already equals ODP
   classic; brights are the softer Flint set (keep).
4. `fuzzel/fuzzel.ini`: `match` + `selection-match` `#9AB8FF` →
   `#98C3FF`. Nothing else.
5. `nvim/lua/plugins/colorscheme.lua`: no palette change (already
   correct). See diagnosis below before touching this file.
6. `dunst/dunstrc`: no change (neutral + red critical already fit).
7. `qt5ct/colors/tmp.conf`: Link `#7AA2F7` → `#61AFEF`, LinkVisited
   `#9AB8FF` → `#98C3FF`. Rename file to `neutral.conf` + update the
   `qt5ct.conf` color_scheme pointer in the same commit.

Net: three files get two-hex tweaks, one file gets a rename, three
files untouched. If the bar and editor look right after that, tag it.

## Why syntax looks plain (diagnose before recoloring)

Our `custom_highlights` contain zero syntax/treesitter groups — all
chrome (Telescope, Snacks, NeoTree, diffs). Syntax color comes purely
from catppuccin's default group links into the overridden palette
roles, which are already colorful. A correct palette cannot fix a
pipeline problem, so check the pipeline live first:

1. `:Inspect` on a dull token — does it show a `@…` treesitter capture
   or only `vim syntax`? No capture = parser missing for that filetype.
2. `:checkhealth nvim-treesitter` / `:TSInstallInfo` — this rebuild has
   no treesitter spec of its own (stock LazyVim only); parsers may never
   have been installed. `:TSInstall <lang>` for the languages in use.
3. `:set termguicolors?` — must be `termguicolors`. If off, everything
   degrades to 256-color approximations (washed out, "plain").
4. `:echo g:colors_name` — must be `catppuccin-mocha`. If the compiled
   cache predates the overrides, `:CatppuccinCompile` once.
5. Scope the complaint: which filetypes look plain? Missing parsers are
   per-language; a global dullness points at (3) or (4) instead.
6. Do not "fix" this with new plugins (rainbow brackets, extra themes).
   If (1)–(4) check out and it still looks plain next to One Dark Pro in
   VS Code, the gap is semantic-token richness, and that is a separate,
   explicitly-scoped decision — not more overrides.

## Non-goals

No palette builder or `palettes/` directory. No contrast-gate tooling
(eyeball it for a few days per rule 1). No wallpaper recoloring. No
GTK theme change (Orchis-Dark-Compact stays). No new statusbar modules
or editor plugins to carry the scheme.
