# Obsidian palette comparison

How the Flint palette maps onto the official Obsidian color system, per
`refs/obsidian-colors.md`. This is reference material for the palette redesign
discussion, not repo documentation.

## Base scale

Official Obsidian dark steps: `00 #1c1c1c`, `05 #212121`, `10 #232323`,
`20 #282828`, `25 #2e2e2e`, `30 #333333`, `35 #3f3f3f`, `40 #555555`,
`50 #666666`, `60 #999999`, `70 #b3b3b3`, `100 #dadada`.

Official Obsidian light steps: `00 #ffffff`, `05 #fcfcfc`, `10 #fafafa`,
`20 #f6f6f6`, `25 #efefef`, `30 #e4e4e4`, `35 #dadada`, `40 #bdbdbd`,
`50 #ababab`, `60 #707070`, `70 #5c5c5c`, `100 #222222`.

### Dark (Flint)

| Raw token | Value | Official step | Status |
| :-------- | :---- | :------------ | :----- |
| `bg` | `#1C1C1C` | base-00 | exact |
| `bg_subtle` | `#212121` | base-05 | exact |
| `surface_0` | `#232323` | base-10 | exact |
| `surface_2` | `#2E2E2E` | base-25 | exact |
| `secondary_alt` | `#333333` | base-30 | exact |
| `surface_1` | `#373737` | none | non-official (between base-30 and base-35) |
| `track` | `#555555` | base-40 | exact |
| `text_faint` | `#666666` | base-50 | exact |
| `overlay_dim`, `overlay_strong` | `#999999` | base-60 | exact |
| `text_muted`, `text_secondary` | `#B3B3B3` | base-70 | exact |
| `text` | `#DADADA` | base-100 | exact |

Departures: `surface_1` is not an official step. `base-20 #282828` and
`base-35 #3f3f3f` are unused. `bg_deep` reuses base-00, which is correct:
Obsidian exposes no step below base-00.

### Light (Sand)

All twelve steps appear exactly once, in order: `bg` base-00, `bg_subtle`
base-05, `secondary_alt` base-10, `surface_2` base-20, `surface_0` base-25,
`surface_1` base-30, `bg_deep` base-35, `border_inactive` base-40,
`text_faint` base-50, `track` and `ring_mid` base-60, `text_muted` and
`overlay_strong` base-70, `text` base-100. The light ramp is complete and
fully official.

## Extended colors

Dark matches all eight official values exactly: `ansi_red`/`error #FB464C`,
`peach #E9973F`, `yellow #E0DE71`, `success #44CF6E`, `accent_cyan #53DFDD`,
`purple #A882FF`, `pink #FA99CD`, and `diff_text #027AFF` for blue.
`ansi_blue #1182FF` has no official counterpart (terminal role).

Light is a mixed pattern. Blue (`#086DDD`), purple (`#7852EE`), and pink
(`#D53984`) match official exactly. Red (`#D22C40`), yellow (`#927000`),
green (`#068036`), and cyan (`#006867`) are darkened versions of the official
values, presumably for contrast as text on light backgrounds. The darkened
values have no official counterpart.

## Accent

The official default accent is `hsl(258, 88%, 66%)`, which resolves to
`#8a5cf5`. Flint's dark `accent_blue #8A5CF5` is that exact color. Light
`accent_blue #6946BC` is a darkened variant for contrast, with no official
counterpart. `selection #8459EA`/`#8458EB` is the accent darkened a few
percent, used as a solid fill; Obsidian's `--text-selection` is an alpha wash
over the base background instead.

## What the docs say about surfaces

The Colors reference defines the semantic model:

- `--background-primary-alt` is the background "for surfaces on top of
  primary background". Obsidian builds elevation upward: surfaces sit on top
  of the chrome and are lighter in dark mode.
- Hover, border, and form-field modifiers are alpha overlays of the base
  scale (`color-mix`/`rgba`), not solid steps.
- `--interactive-normal`/`hover` are the button surfaces. `--text-selection`
  is translucent.

Mapped onto Qt roles, this supports the modernization points raised for the
Qt configs:

| Qt mapping today (dark) | Obsidian convention |
| :---------------------- | :------------------ |
| `Window = base-30 #333333`, `Base = base-00 #1C1C1C` | Elevation upward: chrome darkest, surfaces one or two steps lighter |
| Bevel ramp `base-40 #555555` down to `#000000` | Borders as low-contrast alpha overlays, no pure black |
| `Highlight = solid darkened accent`, `HighlightedText = text` | Selection as accent wash, `--text-on-accent` for the text over it |

The light theme already follows the Obsidian convention (`Window #FAFAFA`
under `Base #FFFFFF`); the dark theme inverts it.
