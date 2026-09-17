# OLED variant spec: pure-black base, rest follows

> Spec only — nothing here is implemented, and nothing in the current tree
> changes because of it. Live truth stays `meta/color-scheme.md`. If this
> variant ever ships, it ships on a branch (see Rollout), never as edits to the
> locked files.

## Goal

A second desktop for OLED panels: every app ground goes pure black `#000000`,
everything else follows without re-deriving the palette. The payoff is per-pixel
light-off (true blacks, lower panel power); on LCD it buys nothing — backlight
bleed turns black into gray — so the neutral ramp stays the default either way.

## The one-line ramp

`base #202020` → `#000000`. Every other step is unchanged:

| Hex       | Role      | OLED fate                                             |
| --------- | --------- | ----------------------------------------------------- |
| `#000000` | base      | was utility-only; becomes the universal ground        |
| `#101010` | crust     | unchanged — gains separation (TabLine on black)       |
| `#171717` | mantle    | unchanged — floats lift harder off black              |
| `#262626` | surface-0 | unchanged                                             |
| `#2D2D2D` | surface-1 | unchanged — the raised state still reads, one step up |
| `#3A3A3A` | surface-2 | unchanged                                             |
| `#5A5A5A` | line      | unchanged                                             |
| text row  | all fgs   | unchanged — contrast rises across the board           |

Why this works with one edit: all tints anchor at surface-1 or above, the
selection tint never touches base, and the one-step rule is relative, so every
relationship in rule 3 survives the move. Contrast on black (computed, not
eyeballed):

| Pair                 | On black | On base today |
| -------------------- | -------- | ------------- |
| text `#D4D4D4`       | 14.2:1   | 11.0:1        |
| subtext `#B3B3B3`    | 10.0:1   | 7.8:1         |
| muted `#8A8A8A`      | 6.1:1    | 4.7:1         |
| text-max `#FFFFFF`   | 21.0:1   | 16.3:1        |
| accent `#48AFFF`     | 8.9:1    | 6.9:1         |
| red-bright `#FF7376` | 8.0:1    | 6.2:1         |

## Per-app deltas (all mechanical)

Every `#202020` ground becomes `#000000`. Exceptions that need thought, not
search-replace:

- `foot.ini`: `alpha=0.9` must become `1.0` — at 0.9 the wallpaper bleeds
  through and black is never black. This kills the SwayFX blur bleed the current
  setup leans on; corners stay square, fine.
- `foot.ini` `regular0=202020` → `000000` (ANSI black == bg, same as today).
- `zathurarc` `notification-error-fg #202020` → `#000000` (fg on red, same role,
  darker).
- `qt5ct` `Base #202020` → `#000000` (text-field grounds go black too).
- `swaylock` inside-colors → black; the blur-darken pipeline already darkens
  20%, keep as is.
- Everything else (`#2D2D2D` selections, `#5A5A5A` borders, all fg text, all
  hues, all tints): byte-identical.

Out of scope for the variant: the LUT wallpaper palette stays as is (chrome-only
variant; wallpapers don't burn power the way grounds do).

## Tooling (designed, not built)

- `meta/palette.py check` needs no change: the swap is base→black and both hexes
  are already in the allowed set.
- A variant mode would only need a writer (`oled` flipping the two hexes per
  file) plus the contrast table above. Not built until rollout.
- Validation is the same loop: `setup --check` (zellij), sway validate, probes,
  pixel-diff screenshots against the neutral desktop.

## Practical-deviation preconditions

The variant inherits the current tree, so these already-fixed collisions must
stay fixed (they were invisible-state bugs, not taste):

- Qt `Highlight` == `Window` (both `#2D2D2D`): selection invisible in KeePassXC
  views — now surface-2, one step above ground per rule 3.
- Zathura `index-active-bg` == `index-bg`, `completion-highlight-bg` ==
  `completion-bg` — now surface-2 for the same reason.
- Standing guard: `#workspaces button.focused:hover` is a deliberate no-op that
  stops the generic hover rule from replacing the solid pill with a translucent
  overlay on hover.
- Accepted: ANSI `bright0` muted doubles as black; `regular0` == bg by
  convention (apps avoid fg-0 on default bg).

## Rollout (if ever)

Long-lived `oled` branch, full-file swap, no `.tmpl` variables (still a
non-goal). Trial by checking out the branch and living in it; merge never — the
variant rebases onto main. Kill criteria: if foot-at-alpha-1.0 looks dead flat,
or if any app hard-codes an assumed-`#202020` blend, the branch dies and this
file records why.

## Open questions

- Burn-in: the bar clock and workspace pills are static bright-on-black.
  Mitigations (dim clock, autohide bar, pixel shift) are undecided and out of
  scope here.
- Whether the LUT wants a darker variant for wallpaper cohesion.
- Whether `mantle`/`crust` should deepen to keep nvim's three depths
  proportional once the floor drops (current call: no — separation grows, which
  is the point).
