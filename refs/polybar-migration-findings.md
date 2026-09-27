# Polybar migration findings (waybar → polybar), 2026-09-24

Self-contained record of every verified fact, decision, and edit for the
thinkpad→optiplex bar migration. Committed to the repo; `refs/fetch-refs.sh`
restores the pruned upstream material. Read this after a
context compaction instead of re-deriving anything, and read
`refs/HANDOFF.md` first for session state and the current checklist.

Context: `thinkpad` runs Sway/Waybar; `optiplex` runs i3/polybar. The waybar
config (`home/dot_config/waybar/config.jsonc` + `style.css.tmpl`) is the
porting source of truth. Polybar cannot run on thinkpad (Wayland, not
installed), so everything here is source/doc-verified; visual verification
happens on optiplex later.

## Documentation / source locations

Everything here is restored by `sh refs/fetch-refs.sh [target-dir]`; each
entry is pinned, so a restore yields exactly the bytes cited below.

- `refs/polybar-wiki/`: clone of `github.com/polybar/polybar.wiki`, HEAD
  `b4f3c9e`.
- `refs/src/polybar/`: full polybar source @
  `b3af5a33166604c689705d7dc67b69c01482d707` (units.cpp, controller.cpp,
  pulseaudio.cpp, …). The `refs/polybar/` rst subset (`polybar.1.rst`,
  `polybar.5.rst`, `tray.rst`) is copied from this tree by the script.
- `refs/src/i3/`: full i3 source @
  `903bcd518df32b0e055b17f5da3f988a0187fd3d` (parser-specs/, bindings.c,
  main.c, …); `refs/i3/*.man` are copied from its `man/` directory.
  `refs/i3/userguide.html` is the rendered page from i3wm.org (tracks the
  latest release, not the pin).
- The rest of the inventory (waybar wiki, sway/SwayFX/rofi/picom/dunst/fuzzel
  man pages, chezmoi reference docs, systemd unit XML, …) is enumerated in
  `refs/fetch-refs.sh`; the reasons for what is deliberately absent are in
  `refs/HANDOFF.md`.

## Why the old spacing was broken (root cause)

- Bar `padding`/`module-margin` parse as `spacing_val`; a BARE NUMBER IS A
  COUNT OF SPACES, not pixels (units.cpp: no unit → `spacing_type::SPACE`).
  Old config: `padding-right = 8` → 8 spaces ≈ 48px right gutter;
  `module-margin = 1` → 1 space ≈ 6px between modules.
- No `[settings] format-padding` existed and no module set `format-*` except
  systray `format-margin = 8px` → every module had zero internal padding and
  text ran together (only the ~6px module-margin space between modules).
- `label-separator = " "` + `label-separator-padding = 8` on xworkspaces were
  DEAD KEYS (see below) → workspace icons had no gaps at all.
- All spacing values in the new config carry explicit `px` units on purpose.

## Source-verified mechanics (polybar b3af5a3)

### Format fallbacks (`src/modules/meta/base.cpp`, `module_formatter::add_value`)

- `formatdef(param, fallback)` = `m_conf.get("settings", "format-" + param,
  fallback)`; per-format keys under the module section
  (`<modname>.<format>-<param>`, e.g. `format-padding`) win over it.
- Covered params: foreground, background, underline, overline, underline-size,
  overline-size, spacing, padding, margin, offset, font.
- ⇒ `[settings] format-padding = 8px` and `format-margin = 1px` are GLOBAL
  fallbacks for every module format; per-module `format-padding`/`format-margin`
  override.

### Bar-level spacing

- `bar.cpp:214`: `module-margin` default is `ZERO_SPACE`; `module-margin-left`
  /`-right` override each side.
- `controller.cpp:510-560`: module-margin is applied only between modules
  (never before the first left-block module), and only renders if set.
- Decision: bar gets NO `padding-*` and NO `module-margin` (defaults = 0).
  The waybar `margin: 1px` per-module rule maps to the settings
  `format-margin = 1px` fallback: inter-module gap = A-right 1px + B-left 1px
  = 2px = two waybar module margins; first module flush like waybar
  `#workspaces { margin: 0 }` handled by xworkspaces override below; right
  edge = dnd's own 1px margin (inside its output, controller adds none).

### Waybar metric mapping (style.css.tmpl line refs)

| Waybar element                              | waybar CSS                     | polybar config                                        |
| ------------------------------------------- | ------------------------------ | ----------------------------------------------------- |
| shared rule (cpu memory clock dnd mpris updates pulseaudio tray) | `padding: 0 8px; margin: 1px` (99-118) | `[settings] format-padding = 8px` + `format-margin = 1px` |
| `#workspaces`                               | `margin: 0; padding: 0 2px` (37-40) | `format-margin = 0`, `format-padding = 2px`             |
| `#workspaces button`                        | `padding: 0 6px` (46-49)       | `label-{active,occupied,urgent,empty}-padding = 6px`   |
| `#window`                                   | `padding: 0 12px; margin: 1px` (171-174) | `format-padding = 12px` (margin from fallback)   |
| `#custom-separator`                         | `padding: 0 0 2px; margin: 0` (164-168) | `format-padding = 0`, `format-margin = 0`         |
| `#tray`                                     | `padding: 0 4px` (214-216)     | `format-padding = 4px`                                 |
| `#tray > widget`                            | `padding: 0 6px` (218-222)     | `tray-padding = 6px`                                   |
| tray icon                                   | `icon-size: 12`, `spacing: 12` | `tray-size = 50%` (of 24px bar = 12px), `tray-spacing = 12px` |

Gap arithmetic verified equal on both sides:

- inter-icon tray = 6+12+6 = 24px both ways.
- tray module edge = 4+6 = 10px both ways.
- workspace edge = 2+6 = 8px both ways.
- between shared modules = 8+1+1+8 = 18px both ways.

### xworkspaces (`src/modules/xworkspaces.cpp`)

- Label keys read: only `label-monitor`, `label-active`, `label-occupied`,
  `label-urgent`, `label-empty` (lines 49-64). No module-level `label` → old
  `label = %icon%` was dead. `label-separator*` exists only in menu/i3/bspwm
  → dead here; removed. Icon gaps now come from
  `label-*-padding` (`load_optional_label` → `load_label` parses
  `<name>-padding`/`-left`/`-right`; label padding renders as builder spacing).
- `enable-scroll` default TRUE (`xworkspaces.hpp:106`; scroll actions emit
  SCROLL_UP/DOWN switching workspaces, cpp:350-352). Waybar's
  `sway/workspaces` has no scroll-to-switch → set `enable-scroll = false`.
- Duplicate module names are allowed (controller `setup_modules` builds a
  fresh instance per occurrence) → the two `separator` entries in
  modules-right are valid.

### Tray (`tray.rst`, `src/x11/tray_manager.cpp:63`)

- `tray-size` = `percentage_with_offset{66., ZERO_PX_EXTENT}` relative to bar
  height, default 66% (≈15.8px at 24px) → `50%` = 12px = waybar icon-size 12.
- `tray-padding` = extent added before AND after each icon (default 0px);
  `tray-spacing` = gap between icons.

### Actions / clicks

- `builder::action` (builder.cpp:321) escapes `:` in commands.
- `tags/action_context.cpp get_actions(x)`: per button, the HIGHEST action ID
  whose range contains x wins. IDs are assigned in parse order
  (`action_open`: `id = m_action_blocks.size()`). Unit test `stacking`
  (`tests/unit_tests/tags/action_context.cpp`) documents nested semantics:
  inner (opened later in the string) wins inside its range.
- `pulseaudio.cpp:110-145 get_output()`: builds the format first, THEN opens
  right/middle/left(EVENT_TOGGLE mute)/scroll wrappers, then `node(output)`.
  In the final string the outer opens precede the format's inner
  `%{A1:pavucontrol:}` ⇒ inner has the higher ID ⇒ **left-click = pavucontrol**
  (matches waybar `on-click: pavucontrol`); the built-in left mute-toggle is
  shadowed: intentional, waybar has no left-mute either. Right-click and
  scroll live on other buttons (per-button map) so they still reach the outer
  wrappers ⇒ adding `click-right = pactl …` works. i3 floats pavucontrol
  (`i3/config.tmpl:145`), same UX as waybar.
- pulseaudio reads `click-middle`/`click-right` only (pulseaudio.cpp:117-126);
  scroll step = `interval` default 5 (m_interval) = waybar `scroll-step: 5` →
  no key needed. Built-in left = mute toggle (overridden by the inner A1 tag).
- Raw action commands execute via `controller.cpp:481`
  `fork_detached(… exec_sh(cmd))` → shell → `~` expands, so
  `click-left = ~/.config/…` works.
- `%{A1:cmd:}` inside `format` is the DOCUMENTED click pattern
  (wiki Formatting.md:375; Known-Issues.md:39 explicitly recommends
  format-level action tags) ⇒ cpu/memory `on-click` ports as
  `format = %{A1:kitty -e btop:}…%{A}`. internal cpu/memory/xwindow read NO
  `click-*` keys, but the format tag needs none. `foot` is thinkpad-only;
  optiplex terminal is `kitty` (and `btop` is in shared pacman.tui).
- script module reads click-left/middle/right, double-click-*, scroll-up/down
  (script.cpp:19-26) → updates/dnd/mpris click parity works.
- `exec`/click commands run via `/bin/sh -c` (process.cpp:129).

### Script modules (repo copies under `home/dot_config/polybar/scripts/`)

- `updates.sh` always emits text: `󰏓 0` in muted `#8A8A8A` at zero updates,
  `󰚰 N` in `#F4BC45` at >0 → module ALWAYS VISIBLE = waybar `.ok` /
  `.has-updates` visible states. Colors match the palette
  (`meta/color-scheme.md`). Uses `checkupdates` (pacman-contrib) + `paru -Qum`.
- `dunst-dnd.sh`: `--toggle` at line 99. It always prints its icon, with
  colors hardcoded to palette (`#FE4864`).
- `mpris.py`: prints a blank line when no player → module collapses
  (the script's own docstring asserts this = waybar `hide-empty-text`). It is
  NOT a chezmoi template (`.py`, no `.tmpl`) so f-string `{{…}}` is safe, and
  the paused state is muted via `%{F#8A8A8A}`.
- waybar's scripts live under `.config/waybar/scripts/` and deploy only on
  thinkpad (`.chezmoiignore`); polybar's under `.config/polybar/scripts/`,
  only on optiplex.

### Text module

- `format = |` on custom/text renders the literal `|` (formatter only
  substitutes `<tag>` placeholders; no `<label>` in the format value) = waybar
  text module `format: "|"`.

### Waybar handler parity reference (config.jsonc)

- mpris: on-click `playerctl play-pause`, on-scroll-up `playerctl next`,
  on-scroll-down `playerctl previous`, restart-interval 5, hide-empty-text.
- pulseaudio: on-click `pavucontrol`, on-click-right
  `pactl set-sink-mute @DEFAULT_SINK@ toggle`, scroll-step 5.
- cpu/memory: on-click `foot -e btop`, interval 5.
- updates: interval 3600, signal 8 (RTMIN+8 sent by toggle_topgrade.sh),
  on-click `~/.config/sway/scripts/toggle_topgrade.sh`.
- dnd: interval 5, signal 9, on-click `dunst-dnd.sh --toggle`.
- clock: no on-click (tooltip only). battery: thinkpad-only.

## Picom: earlier revert plan CANCELLED (correction)

The earlier plan to restore `blur-background-exclude`/`shadow-exclude` lists
removed by `28f262b` was WRONG and was not carried out. `picom.conf.tmpl`
`rules:` blocks (present since before 28f262b) already set
`blur-background = false; shadow = false` for `_GTK_FRAME_EXTENTS@` and for
`window_type = 'dock' || 'desktop'`; 28f262b only deleted the redundant
legacy exclude lists. polybar is a dock → no shadow/blur either way.
No picom change was made. Flag for veto if the user disagrees.

## Waybar CSS hover bug from `28f262b` (fixed in this pass)

- 28f262b inserted `#custom-updates.ok { color: muted }` into the MIDDLE of
  the 8-selector hover group, splitting it into two rules:
  - rule 1: `[battery, clock, cpu, custom-dnd, custom-mpris]:hover` +
    `#custom-updates.ok` → only `color: muted` ⇒ hovering those five modules
    dimmed the text instead of the hover treatment (text-max + hover bg +
    border), and they lost bg/border entirely;
  - rule 2: `[custom-updates, memory, pulseaudio]:hover` → full treatment
    (accidentally correct for these three).
- Fix: `#custom-updates.ok` moved BEFORE the complete 8-selector hover rule.
  Specificity tie (`#custom-updates.ok` = `#custom-updates:hover`, both
  id+class) → later rule wins → at rest `.ok` is muted, on hover the full
  hover treatment applies. `#custom-updates.has-updates` / `.has-updates:hover`
  (later in the file, higher specificity) unchanged and still win for the
  warning state.

## Edits applied in this pass

1. `home/dot_config/polybar/config.ini.tmpl`:
   - `[bar/main]`: removed `padding-left = 0`, `padding-right = 8`,
     `module-margin = 1` (space-unit bugs; defaults are 0).
   - `[settings]`: added `format-margin = 1px` + `format-padding = 8px`
     (waybar shared rule) with an intent comment.
   - `[module/xworkspaces]`: removed dead `label = %icon%`,
     `label-separator`, `label-separator-padding`; added
     `format-margin = 0`, `format-padding = 2px`, `enable-scroll = false`,
     `label-{active,occupied,urgent,empty}-padding = 6px`.
   - `[module/xwindow]`: added `format-padding = 12px`.
   - `[module/custom/mpris]`: added `click-left = playerctl play-pause`,
     `scroll-up = playerctl next`, `scroll-down = playerctl previous`.
   - `[module/cpu]` / `[module/memory]`: `format` now wraps content in
     `%{A1:kitty -e btop:}…%{A}` (waybar on-click parity, kitty adaptation;
     comment on cpu explains).
   - `[module/custom/updates]`: added
     `click-left = ~/.config/i3/scripts/toggle_topgrade.sh`.
   - `[module/pulseaudio]`: added
     `click-right = pactl set-sink-mute @DEFAULT_SINK@ toggle` (format-volume
     A1 pavucontrol tag kept: verified it wins for left-click).
   - `[module/systray]`: removed `format-margin = 8px`; added
     `format-padding = 4px`, `tray-padding = 6px`, `tray-size = 50%`
     (kept `tray-spacing = 12px`) + intent comment.
   - `[module/custom/dnd]`: added
     `click-left = ~/.config/polybar/scripts/dunst-dnd.sh --toggle`.
   - `[module/separator]`: added `format-padding = 0`, `format-margin = 0`
     (override the settings fallback to match waybar) + comment.
   - `[colors]`: removed unused `yellow` (no `${colors.yellow}` anywhere;
     scripts hardcode their own palette hexes).
2. `home/dot_config/waybar/style.css.tmpl`: `.ok` rule moved before the
   restored single hover group (see bug section).
3. `data/packages.json`: removed `waybar` from `pacman.desktop` (still in
   `machines.thinkpad`); made two notes machine-neutral: `pacman-contrib`
   now serves the bar updates module on both machines, `mpv-mpris` feeds the
   bar mpris module on both. `cliphist` left in place (Wayland-only; optional
   drop for optiplex, flagged not changed).
4. `home/.chezmoiignore`: added `.config/waybar` to the optiplex block
   (symmetric with `.config/polybar` in the thinkpad block).
5. `home/dot_config/i3/scripts/executable_toggle_topgrade.sh`: comment now
   names polybar as the caller (the Waybar claim was already stale: waybar
   uses the sway copy); removed dead `sh -c 'topgrade; pkill -RTMIN+8 waybar'`
   → `kitty --name $app_id -e topgrade` (waybar never runs on optiplex; i3
   `for_window [instance="topgrade_term"]` at config.tmpl:150 unaffected).

## Known gaps (deliberately not fixed; report to user)

- **Separator vertical nudge**: waybar `padding: 0 0 2px` gives 2px of bottom
  padding, while polybar format padding is horizontal only, so the `|`
  baseline can't be nudged.
- **cpu/memory click opens a tiled window** unless i3 gets a for_window rule.
  Waybar's `foot -e btop` is likewise unmanaged on thinkpad (sway has no btop
  rule), so verify the desired float behavior on optiplex.
- **Battery module absent** in polybar: intentional, optiplex is a desktop
  (waybar battery is thinkpad hardware).
- **Window title icon**: waybar's `sway/window` shows a window icon
  (`icon: true`, 14px); polybar's `custom/window` is text-only (its
  rewrite rules and 72-column cap are ported, see item 12).
- **Workspace icon font-size 16px** (waybar `#workspaces button label`) vs
  polybar single `font-0 … size=10`: per-label font size unverifiable from
  thinkpad → left as is; check visually on optiplex.
- **Hover styling**: waybar `:hover` bg/border/transition effects have no
  polybar equivalent (only `cursor-click = pointer`).
- **Tooltips**: waybar clock/mpris/cpu/memory tooltips don't exist for polybar
  script/text modules (tray context menus are native and work).
- **cliphist** still installed on optiplex via shared `pacman.desktop`
  (Wayland-only tool): optional cleanup, not changed.

## Visual verification checklist (run on optiplex)

1. `make lint` and `chezmoi diff` clean (thinkpad side).
2. On optiplex: restart polybar (or re-login); check:
   - ~8px bar-right gutter (was ~48px), modules separated by 2px with 8px
     internal padding (shared), workspace icons with 12px gaps and 8px left
     edge, window title 12px padding, tray icons 12px tall with 24px gaps and
     10px module edge, separator `|` flush (no 8px padding).
   - Clicks: workspace icon click focuses. cpu/memory open `kitty -e btop`.
     updates click opens topgrade scratchpad. pulseaudio: left opens
     pavucontrol (floating), right mutes, scroll changes volume by 5%. tray
     icon menus. dnd click toggles + recolors to red. mpris: click play-pause,
     scroll next/prev (only while a player shows).
   - Scroll over workspaces must NOT change workspace (`enable-scroll=false`).
   - Hover/waybar checks: `#custom-updates.ok` muted at rest, full hover on
     hover; battery/clock/cpu/dnd/mpris hover restored (thinkpad, waybar).
3. Font `SauceCodePro Nerd Font Mono` = `ttf-sourcecodepro-nerd` in
   pacman.fonts ✓ installed both machines.

## Verification results (this pass)

All checks run on thinkpad after the edits; everything passed:

- `chezmoi execute-template` renders of `config.ini.tmpl`, `style.css.tmpl`,
  `.chezmoiignore`: clean, no unrendered `{{`.
- Rendered polybar config parsed with `configparser.RawConfigParser(strict=True)`:
  14 sections, with these assertions confirmed:
  - bar has no `padding-left/right`/`module-margin`.
  - `[settings]` has `format-margin = 1px` + `format-padding = 8px`.
  - xworkspaces has `format-margin = 0`, `format-padding = 2px`,
    `enable-scroll = false`, four `label-*-padding = 6px`, and no
    `label`/`label-separator*` keys.
  - xwindow `format-padding = 12px`.
  - systray `4px`/`6px`/`12px`/`50%` and no `format-margin`.
  - separator `0`/`0`.
  - cpu and memory formats contain `%{A1:kitty -e btop:}`.
  - updates `click-left` = i3 toggle path.
  - pulseaudio keeps the pavucontrol A1 tag and has the pactl `click-right`.
  - mpris has the three playerctl bindings.
  - dnd `click-left` has `--toggle`.
  - `[colors]` = the 6 used keys (no `yellow`), and every `${colors.*}`
    reference in the file resolves to a defined key.
- Rendered waybar CSS: `{`/`}` balanced (37 each). `#custom-updates.ok` rule
  precedes the hover group. The hover group is the single 8-selector list
  (battery/clock/cpu/dnd/mpris/updates/memory/pulseaudio) with `.ok` absent
  from it, and `.has-updates:hover` still comes after.
- `data/packages.json`: valid JSON. `waybar` gone from `pacman.desktop`,
  still in `machines.thinkpad`. Both touched notes mention waybar + polybar.
- `.chezmoiignore`: `.config/waybar` is inside the optiplex block,
  `.config/polybar` inside the thinkpad block. The template renders on
  thinkpad.
- `sh -n` on `executable_toggle_topgrade.sh`: clean; no `waybar` string left
  in the script.
- `make lint`: passed (prettier).
- `chezmoi diff`: `.config/waybar/style.css` shows exactly the hover-group
  fix. Two other entries are NOT from this pass: (1) the onboarding
  `run_onchange` script is pending re-run because it embeds
  `sha256(packages.json)`: hash moved `fba21fcb…` → `2db06156…` with the
  waybar package removal, which is that script's designed trigger; (2)
  `.local/bin/chezmoi-drift-check` differs from the machine copy:
  pre-existing user/machine drift (static file, last touched by commits
  `d5bccdc`/`3738184`), flagged to the user, not modified here. The polybar
  config and i3 script are machine-ignored on thinkpad, so they are verified
  via direct `execute-template` + parser assertions instead of `chezmoi diff`.
- Script-runner collapse semantics re-verified in source:
  `command<REDIRECTED>::readline()` uses `std::getline` (strips the newline),
  and `script_module::get_output()` (script.cpp:96) returns `""` when
  `output.empty() && exit_status == 0` → mpris's blank line and any empty
  output hide the module (waybar `hide-empty-text` parity). Runner reads only
  the first line for non-tailed scripts, and all three repo scripts emit a
  single line, so this is fine.

Not verifiable on thinkpad (polybar cannot run under Sway/X-less): actual
pixel spacing, tray icon rendering, fonts, and click behavior: use the
optiplex checklist above.

## Round 2: full thinkpad → optiplex port audit (bindings/scripts/units/packages)

Four parallel editing passes over disjoint scopes, then a source-level review
of every load-bearing claim. Validated by template render + `sh -n` + strict
INI parse + `make lint`; i3/polybar runtime checks remain optiplex-only.

### Changes

**i3 config** (`home/dot_config/i3/config.tmpl`)

- `$mod+Shift+c` now runs `reload, exec --no-startup-id polybar-msg cmd
  restart`: sway's reload restarts waybar via `bar {}`; i3's reload did
  nothing for polybar. Verified from i3 source: `commands.spec`
  `'reload' -> call cmd_reload()` returns to INITIAL, `commands_parser.c`
  treats `,`/`;` as command separators, `bindings.c run_binding` copies the
  command buffer before executing so a reload mid-chain cannot free the rest
  of the command.
- `--release` added to the three toggle bindings: caffeine (`$mod+Shift+i`),
  drop term (`$mod+grave`), dnd (`$mod+Shift+d`): sway has `--no-repeat`, i3
  has no such flag (`config.spec` state BINDING offers only
  `--release/--border/--whole-window/--exclude-titlebar`). i3 enables XKB
  detectable autorepeat (`main.c`), so held keys emit only repeated
  KeyPress; a `--release` binding fires exactly once per physical press.
  Matches the pre-existing `--release $mod+d` rofi convention.
- `border normal` added to the scratchpad drop-term/topgrade `for_window`
  rules: sway gives those rules a titled border. i3's default here is
  `default_border pixel 1` (frameless), so the drop term had no titlebar.
- New startup line `exec --no-startup-id mkdir -p
  $HOME/Pictures/Screenshots`: sway's `helper_capture.sh` mkdirs the save
  dir before use. The Print binding calls `flameshot full -p` directly and
  flameshot does not create the directory.

**polybar config** (`home/dot_config/polybar/config.ini.tmpl`)

- New `[module/i3mode]` (`internal/i3`) between xworkspaces and custom/mpris,
  porting waybar's `sway/mode` chip. `format = <label-mode>` only; polybar
  source proves at-rest invisibility: `i3.cpp build()` emits the label only
  when `m_modeactive`, and `base.cpp decorate()` flushes an empty output
  before any margin/padding, so the bar at rest is pixel-identical to before.
  `label-mode = 󰘳 %mode%`, yellow on warning-hover, `format-font = 2` →
  font-1 bold. All of it is mapped 1:1 from waybar `#mode` CSS (padding
  comes from the `[settings]` `format-padding` fallback; the 1px vertical
  margin and 1px border have no polybar equivalent). `format-font`/
  `format-margin`/`format-padding` are real keys (`base.cpp` parses
  `name + "-font"` with `name="format"`; `[settings] format-*` are global
  defaults via `formatdef` at `base.cpp:91`).
- `enable-ipc = true` confirmed in `[bar/main]` (required by the reload
  chain). New `[colors]` keys `yellow`, `warning-hover` (palette-templated).

**i3 scripts**

- `lock.sh.tmpl` `--now` branch rewritten to honor the xss-lock contract
  ("the command should not fork"): previously the script backgrounded the
  locker and exited, which on the idle path meant xss-lock re-ran it every
  screensaver cycle, made forced unlock a no-op, and drifted LockedHint.
  Now, when `XSS_SLEEP_LOCK_FD` is set: spawn i3lock from a subshell that
  closes its copy of the fd first, then close our own copy, matching the
  upstream `transfer-sleep-lock-i3lock.sh` example verbatim ("close our fd
  (only remaining copy) to indicate we're ready to sleep"). The fd, not
  process exit, gates logind (delay locks cap at `InhibitDelayMaxSec`; an
  i3lock that inherits the fd and never closes it would cost that cap on
  every suspend). Then `wait` for the locker; a TERM/INT trap pkills
  i3lock-color so xss-lock's forced unlock still works; cleanup runs only
  after the screen is really unlocked. The no-fd case (xss-lock idle path)
  uses the same wait logic.
- `power_control.sh`: suspend action is `systemctl suspend` alone:
  xss-lock's own `lock.sh --now` instance locks on PrepareForSleep and
  the sleep-lock fd gates sleep. (Launching a second locker here raced
  that instance on the shared capture file, which could paint the lock
  background white.) sway's copy keeps the sequential string because
  sway's `lock.sh --now` returns at once (backgrounds swaylock
  internally).
- `flameshot_gui.sh`: `mkdir -p` the save dir before `flameshot gui -p`.
  `flameshot_window.sh`: `--region` now takes the documented `WxH+X+Y` form:
  `+X,Y` was rejected, so the window-capture region flag never applied.
- `mpris.py`: state handling ported; status selection was **not** aligned
  with waybar's: bare `playerctl status` resolves a different player than
  the metadata query (fixed in the "Acceptance round" below). polybar still
  hides non-Playing/Paused immediately (a one-shot script cannot do waybar's
  hide-after-grace window, an accepted platform limit).

**systemd / packaging / ignore**

- `calibre-sync-netmon.service`: `After`/`PartOf`/`WantedBy` now name both
  session targets: the unit is symlinked into *both* `*.wants` dirs but
  previously only stopped itself on thinkpad (optiplex logout left it
  running with stale session env). Entries for the absent target are inert
  on each machine.
- `data/packages.json` `machines.optiplex`: added `xss-lock` and
  `xorg-xset`: the i3 idle path (`xset s`, `xset dpms`, xss-lock at
  `config.tmpl` startup) and `toggle_idle.sh` call both, but neither was in
  any list; a fresh optiplex would boot with a broken idle/caffeine path
  (`pactree -r` confirms nothing pulls xset in). Expect the onboarding
  `run_onchange` script to re-run on next apply (hash moved to
  `2d9fa50b…`) and report the two new installs, by design.
- `.chezmoiignore`: comment at `wlsunset.service` documenting that
  `wlsunset-env.service` intentionally stays deployed on optiplex:
  `redshift.service` has `Wants=wlsunset-env.service` and reads the env file
  it generates. (The audit instruction to "fix" its absence from the
  optiplex block was correctly rejected after verifying the consumer; the
  unit is shared.)

### Verified-claim ledger

- i3 has no `--no-repeat`: `parser-specs/config.spec` state BINDING.
- `--release` fires once per press: `main.c` enables
  `XCB_XKB_PER_CLIENT_FLAG_DETECTABLE_AUTO_REPEAT`; with detectable
  autorepeat there are no synthetic KeyRelease events during a hold.
- `reload, exec …` chains: `commands.spec` + `commands_parser.c` (`,`, `;`
  separators) + `bindings.c run_binding` copy-before-execute.
- `polybar-msg cmd restart` works: `enable-ipc = true`, only bar is `main`.
- i3mode at-rest invisibility + bold: `i3.cpp build()`, `base.cpp decorate()`
  empty flush, `format-font = 2` → `%{T2}` → `fns[t.font - 1]` font-1.
- xss-lock fd contract: xss-lock(1) ("The locker should close this file
  descriptor to indicate it is ready") + upstream
  `transfer-sleep-lock-i3lock.sh` (spawn with `{FD}<&-`, then close ours).
- `wlsunset-env.service` shared: `redshift.service` `Wants=` +
  `EnvironmentFile=%h/.config/wlsunset.env`.

### Platform-justified, deliberately not ported (no edits)

- Media keys without `--locked` (lock.sh correctly documents i3lock-color
  `--pass-media-keys`), flameshot vs grim/slurp/satty pipeline,
  xss-lock/xset vs swayidle, feh/.fehbg vs awww, redshift vs wlsunset units,
  `tiling_drag`/`popup_during_fullscreen`/Gtk file-chooser rules, no X11
  twin of the 10s pre-lock idle warning (`helper_idle_*` stay sway-only per
  AGENTS: optiplex has no idle suspend), touchpad `input` block, waybar
  tooltips/hover styling (polybar cannot).
- `cliphist` referenced nowhere on either machine, so parity holds. Optional
  drop from the shared package list reported, not done (user's call).

### Open questions reported for optiplex (no edits made)

- GTK CSD blur/shadow exclusion: resolved by the current `rules:` block.
  `_GTK_FRAME_EXTENTS` windows get `blur-background = false` and
  `shadow = false` (the standalone `blur-background-exclude` /
  `shadow-exclude` arrays were removed in `28f262b`).
- picom `corner-radius` vs waybar's 4px chip corners: resolved by the
  current values. The global radius is `4` (matching the chips); only the
  tooltip rule sets `8` ("typed tooltips keep their own corners").
- dunst shadow strength vs thinkpad: still open, needs a visual look,
  report only.
- polybar must be built `+i3` for `custom/i3mode`, verified on optiplex:
  `polybar -vvv` includes `+i3`.

### New optiplex verification checklist (after `git pull`)

1. `i3 -C -c ~/.config/i3/config`: parses the new `reload, exec …` chain
   and the `border normal` rules.
2. `$mod+Shift+c` after a polybar config edit: polybar restarts and picks
   up the change, with no duplicate bars.
3. `$mod+r` then `h/j/k/l`: the `󰘳 resize` chip appears left of mpris,
   bold yellow-on-dark; Return/Esc hides it and the bar returns
   pixel-identical (no stray gap between workspaces and mpris).
4. Hold `$mod+Shift+d` (~1s): DND toggles exactly once; same for
   `$mod+Shift+i` and `$mod+grave` (drop term shows once, no flicker).
5. Drop term and topgrade term float with a titlebar and still match
   `instance="scratchpad_term"` / `topgrade_term`.
6. Suspend three ways, locked before sleep every time: (a) the power menu
   (power_control `&` path), (b) `systemctl suspend` from a terminal
   (xss-lock fd path), (c) idle `xset s 30` timeout (xss-lock idle path:
   the script now blocks until unlock). On wake, DND restores to its
   pre-lock level unless the double-instance case ran (power_control +
   xss-lock). That quirk exists on sway too and is accepted.
7. Print / Shift+Print / Ctrl+Print all save into `~/Pictures/Screenshots`
   (dir now created at startup); window capture no longer errors on
   `--region`.
8. Log out/in on optiplex: `calibre-sync-netmon` stops with
   `i3-session.target` on logout.
9. Next apply re-runs onboarding (packages.json hash) and reports
   `xss-lock`, `xorg-xset` as new installs, by design.
10. `polybar -vvv` includes the i3 module build flag.

### Verification results: 2026-09-25 (optiplex)

Checklist: 1–5, 7, 9, 10 verified; **6 and 8 still pending** (both need
real suspend/logout cycles; 6 was additionally blocked by the broken
lock chain fixed in "Post-reboot lock round" below: retest it against
the fixed locker. Before 6(c) note `xset s` reads `0` and DPMS is
disabled: caffeine is on, so re-enable the screensaver timeout first).

1. ✓ `i3 -C` exit 0: reload chain, `border normal`, `--release`
   bindings.
2. ✓ `$mod+Shift+c` runs `reload, exec polybar-msg cmd restart`; exactly
   one bar before and after, polybar PID stable across the restart.
3. ✓ `$mod+r` → resize chip renders bold amber on `warning-hover`, in
   place between `xworkspaces` and `custom/mpris`; Return/Esc hides it
   and the bar is pixel-identical at rest.
4. ✓ Hold-key: DND `0→50→0`, caffeine `0→30→0`, drop term toggles
   exactly once (still a single `scratchpad_term`).
5. ✓ Both scratchpads float with a titlebar. Drop term: frame
   `171,128 1024×537` vs client `173,148 1020×515` (`window_rect.y = 20`).
   Topgrade term exercised with a `kitty --name topgrade_term -e sleep`
   stand-in: the `for_window [instance="topgrade_term"]` rule applies
   mark + float + `75×70 ppt` + center with the same geometry. Related
   observation: i3 `kill` on a kitty that has a foreground command
   running surfaces kitty's default `confirm_os_window_close = -1`
   prompt (window titled "Close OS window") instead of closing at once;
   at a shell prompt it closes directly. Default kept (it protects runs
   like topgrade).
7. ✓ Print / Shift+Print / Ctrl+Print flows write into
   `~/Pictures/Screenshots`; region capture works.
9. ✓ Apply re-ran onboarding and reported `xss-lock`, `xorg-xset` as new
   installs (by design).
10. ✓ `polybar -vvv` includes `+i3`.

Fix verification (HANDOFF round fixes):

1. ✓ Rofi: glyph hugs the input text. Box inset 16px left/right and 8px
   top/bottom. 2px prompt spacing (fuzzel geometry).
2. ✓ Power confirm: `Enter=yes, Esc=no` renders inside the input box
   after `confirm suspend? `; Esc/arrow cancel works (Enter deliberately
   not pressed, since it would suspend).
3. ✓ Dunst: deploys `offset = (8, 32)` and renders below the 24px bar.
   **DPI deviation (reported, not compensated):** X11 dunst scales
   offsets by 1.0625 (102 vs 96 DPI), so `offset_y 32` renders its top
   edge at y=34 (2px low), the 8px right margin renders 9px (1px), and
   `offset_x = 8` can never render as 8 (7→7, 8→9). Wayland/thinkpad is
   unaffected; the deployed offset stays `(8, 32)` per user decision.
4. Deferred: the waybar muted dim is thinkpad-only. Verify when back on
   thinkpad.
5. ✓ Diagnosed below; config stays `(0, 2)`.

#### Picom shadow geometry (fix 5 diagnosis)

The stale-instance hypothesis is rejected: the running process is
`picom --config ~/.config/picom.conf` (single instance; config mtime
predates the start), `shadow-opacity 0.5` measured applied, and the
offset keys are honored (`60,60` extends the right reach to +83px).
Build: `picom v13 git rev d87a5ba`. Each row is a shadow-on vs
shadow-off pixel diff; the control region (x20–60, y130–664) reads
bit-exact 0.000 every run, and `blur-background` on/off changes nothing:

| offset | left | top | right | bottom |
|---|---|---|---|---|
| `0,0` | 0 | 0 | — | 0 (renders no shadow) |
| `0,2` (deployed) | 0.000 | 0.083 | strong ≈22px | strong ≈24px |
| `-8,-8` (two runs) | 0.00 | 0.07 | 0.57 ≈ 0 | 0.000 (no shadow at all) |
| `-20,-20` | strong ~17px ramp | strong ~17px ramp | 0.25 ≈ 0 | ≈0 (fades out by y671) |
| `60,60` | — | — | core + tail to +83px | — |

Shadow tails render only where the shadow core reaches the window edge:
right/bottom need offset ≥ 0, left/top need ≥ ~14px protrusion. Those
requirements are contradictory, so **no single offset can produce a
four-sided (centered) shadow on this build**: only the diagonal pair
changes. Decision: keep `(0, 2)` (the documented thinkpad-mirror intent)
and report the renderer limitation; no config change.

### Post-reboot lock round: 2026-09-25 (optiplex)

The first real exercise of the lock chain (item 6 prep) exposed the
following; each is fixed, applied, and verified:

1. **Wrong locker binary.** `lock.sh` called `i3lock-color`, but that
   package installs its binary as `i3lock`, so every lock path (manual
   `$mod+Shift+x`, power-menu suspend, `systemctl suspend`, and idle via
   xss-lock) died with command-not-found. Invocation, `pkill`
   trap, and comments now use `i3lock`; a `getopt` probe confirms every
   other flag is accepted by the installed build.
2. **DND stranded at pause 100.** The failing locker aborted the script
   under `set -e` before `cleanup()`, leaving dunst paused at 100 (above
   the 90-level bypass rules), so all later notices (e.g. the caffeine
   toggle) were swallowed. `run_lock || true` guarantees
   cleanup; pause was reset to 0 and observed back at 0 with
   `pause_file` removed after both a scripted and a real lock/unlock
   cycle.
3. **Idle "timer does not exist".** Boot arms `xset s 30`, but the
   stateless caffeine toggle had silently flipped it off while its
   notice was suppressed by (2), and idle could not lock anyway because
   of (1). No code change beyond the above; `xset s` reads `0` and DPMS
   disabled whenever caffeine is on.
4. **Confirm list leading gap.** The rofi theme's fixed
   `element-icon { size: 1em; }` reserves an icon column that dmenu
   choices never fill: row text rendered at x=451 instead of x=434
   (17px, measured). `confirm_menu` now passes
   `-theme-str "element-icon { size: 0px; }"`; the drun launcher keeps
   its icons, and a real-script capture confirms flush rows.
5. **Notice glyph parity.** The lock notice now carries `U+F023` and
   all five caffeine failure notices `U+F530`, byte-identical to the
   thinkpad sources; dnd notices already matched and power-confirm has
   no icon on either machine. dunst renders them with
   `SauceCodePro Nerd Font Mono 10`.
6. **Background and indicator.** i3lock scales the image only when a
   placement flag is given; its default draws at native size top-left,
   putting the 451×253 downscaled capture in a corner over white:
   `--fill` fixes it (zero white pixels in the render). Per request the
   indicator is compacted: radius `120→72`, ring `4→3`, time `24→16`,
   date `24→12`, and `--verif-font`/`--wrong-font` plus sizes set to
   the Nerd Font, since those status texts defaulted to sans-serif.
   The ring measures 155px vs 259px before; the verif/wrong state is
   too transient for the screenshot path (both capture attempts landed
   outside it), so that font rests on the `i3lock(1)` mapping.

### Scratchpad and suspend round: 2026-09-25 (optiplex)

Two reported issues plus a requested indicator tweak; each fixed,
applied, and verified:

1. **`$mod+minus` did nothing.** `cycle_scratchpad.sh` located
   `__i3_scratch` at `.nodes[].nodes[]`, but it hangs under the `__i3`
   pseudo-output one level deeper, so hidden windows classified as
   visible and the script issued `[con_id=<wrapper>] scratchpad show`:
   i3 matches criteria against window leaves and rejects a
   `floating_con` id with `ERROR: (null)` (reproduced on live ids). The
   script now walks the tree carrying inherited scratchpad state,
   detects the workspace by name, and emits leaf ids (marks live on
   leaves too: the drop_term exclusion previously checked markless
   wrappers). Verified with the deployed script: a test window showed
   on run 1 and hid again on run 2.
2. **White lock background: two lockers, one capture.** power_control's
   suspend ran `lock.sh --now &` alongside xss-lock's PrepareForSleep
   instance, and both imported to the same `i3lock_bg.png`. Suspend is
   now `systemctl suspend` alone (xss-lock's instance locks, its fd
   gates sleep); lock.sh captures to a per-instance `i3lock_bg_$$.png`,
   writes the pause file first-wins via `pause_owner` (only the writer
   restores), and `timeout`s the `import`. Verified with two
   overlapping lock.sh runs: both captures coexisted, pause held at 100
   until the owning instance cleaned up, and pause/file/image all
   cleared after unlock.
3. **Indicator retuned per request:** radius `72→84`, time `16→18`,
   date `12→14`, verif/wrong `13→14`; ring stays `3`.

### Acceptance round: 2026-09-26 (optiplex)

Full feature acceptance pass over the i3/polybar migration; each item
applied, exercised on i3, and evidenced under `/tmp/opencode/shots/`:

1. **Systray sizing finalized:** `tray-size = 66%` + `tray-spacing = 6px`.
   nm-applet shears a fixed 16px icon per `tray-size`; 66% renders it at
   its 16px natural size on this 24px bar (the waybar reference look).
   No upstream fix exists (polybar #2933, #1603/#525/#794/#854/#1143/
   #1813/#2741); spacing 6px came from the size sweep. Icon order
   reshuffles on bar restart (XEMBED arrival order), which is cosmetic.
2. **flameshot scripts rewritten and retested:** xdotool's
   `--onlyvisible --class flameshot` always matches the always-visible
   9×9 tray window, so the old wait loop never saw the GUI close; the
   `windowactivate` step is gone and `flameshot gui` stays interactive by
   design (SIGTERM on the gui client wedges the daemon: restart it, and
   confirm/cancel through the overlay instead). Retested both bindings:
   Ctrl+Print saves the focused-window region (45→46 files, client
   exits, daemon alone remains), Shift+Print overlay cancels on Escape
   with no file written.
3. **MPRIS status gate:** bare `playerctl status` resolves chromium
   (first in `-l`) while the metadata query resolves mpv, so idle
   chromium's `Stopped` collapsed the module during playback. Status now
   comes from `playerctl metadata --format {{status}}`: same player
   selection as artist/title. Verified across playing, paused,
   chromium-only, and killed states (module renders, then collapses to
   an empty line).
4. **MPRIS paused color tag:** the port emitted `%{F##8A8A8A}` (MUTED
   already carries `#`); polybar leaked a literal `}` before the icon and
   ignored the color. Fixed to `%{F#8A8A8A}`: muted gray now applies
   (text-zone mean 0.147 vs 0.162 for white) and the `}` is gone.
5. **MPRIS italic parity:** waybar wraps the whole paused label in `<i>`;
   polybar needs a font slot, so `font-2 = …:style=Italic` was added and
   the script wraps paused output in `%{T3}…%{T-}` (T-index is 1-based,
   `%{T-}` resets; font-2 loads `SauceCodeProNerdFontMono-Italic.ttf`).
   Confirmed on the bar.
6. **Idle lock leg verified (checklist 6, xset side):** DND on
   (pause 50) → `xset s 10` → xss-lock ran `lock.sh --now` → i3lock up
   with pause 100 → kill i3lock → pause restored 50 → DND off (0), and
   xset returned to `timeout 0` / DPMS Disabled. The power-menu and
   `systemctl suspend` legs were later user-tested with real suspend
   cycles (journal, 00:08; both reported working). Item 8's logout cycle
   remains the user's call (the i3-session.target stop/start substitute
   passed).
7. **Reported gap (scratchpad restore hotkey):** `$mod+Shift+space` was
   plain `floating toggle`; on a shown scratchpad window it tiled the
   window but kept the scratchpad's `border normal` titlebar. The binding
   now execs `toggle_floating.sh`: a focused window whose inherited
   `scratchpad_state` is set (the cycle script's detection) is restored
   with `move container to workspace current, floating disable, border
   pixel 1`: it leaves `__i3_scratch`, lands tiled on the current
   workspace with the `default_border pixel 1`; every other window still
   gets a plain floating toggle (round-trip verified: restore →
   `user_off`/`pixel`/workspace, toggle → `user_on`, toggle →
   `user_off`). i3-only for now: sway has the same gap and is not
   installed on this machine, so its port waits for the thinkpad session.
8. **Reported gap (no warning before the idle lock):** sway warns at
   20s and locks at 30s (`helper_idle_warning.sh` + resume dismiss); the
   i3 path locked instantly (its locker skipped the notify/delay on
   purpose: suspend must not be delayed). Ported through
   xss-lock's native `--notifier`: boot arm and `toggle_idle.sh` now use
   `xset s 20 10` (was `xset s 30`, leaving the default cycle 600), so
   the notifier runs at the 20s activation and the locker after the 10s
   cycle, the same 20s-warning/30s-lock window as sway. The new
   `idle_notifier.sh` reads the cycle from `xset q` (it *is* the
   countdown), shows the sway-identical dunstify payload (`-a
   idle-warning -u low -p`, `screen locking in Ns`), and closes it on
   xss-lock's SIGHUP (user activity) or SIGTERM (locker starting); a
   zero cycle never runs it (xss-lock behavior). Live-verified:
   notifier process alive inside the grace window, `dunstctl count
   displayed` 0→1 on the exact payload, in-window activity cancelled the
   lock, a fresh idle cycle locked at the designed time, pause returned
   to 0 with the pause file removed. Operational caveat: xss-lock must
   start inside the session: relaunched from a bare shell it aborts on
   `NoSessionForPID`/`logind_session` assertion, so use
   `i3-msg 'exec --no-startup-id xss-lock --notifier=… -- …'`.
9. **Sweep follow-up (desktop entries fixed):** `btop`/`nvim`/`zellij`
   `.desktop` files and the `x-scheme-handler/terminal` default
   hardcoded `foot`, which exists only on thinkpad; all four now branch
   on hostname (`kitty` on optiplex). Remaining sweep items reported,
   not fixed (impossible or N/A on this machine): (g) the touchpad
   input block is thinkpad-only (no touchpad on this desktop), and
   polybar renders no waybar-style tooltips. The actionable three,
   (b), (c), and (h), are item 11 below; (a), (d), (e), and (f) are
   fixed in item 12.
10. **Reported gap (no final `locking screen...` beat):** the countdown
    showed but the sequence ended silently at lock time. Sway's idle
    timeout runs `lock.sh` (notify + 2.5s + lock) and reserves `--now`
    for before-sleep; i3's xss-lock uses one locker for both idle and
    sleep, so it had to stay delay-free. The discriminator is xss-lock's
    own contract: `XSS_SLEEP_LOCK_FD` is set *only* when the reason is
    system sleep. `lock.sh.tmpl` now keys the notify/delay skip off that
    fd instead of a `--now` flag (whose only caller was the xss-lock
    line, now dropped from `config.tmpl`), and every path shares the
    backgrounded run with the TERM→kill-i3lock trap (the old foreground
    branch had none). Live-verified all three paths: idle = countdown
    painted → SIGTERM closes it → beat painted at cycle end → i3lock at
    cycle-end+2.5s. Manual = `displayed@1s=1`, i3lock at t3s. Sleep sim
    (`XSS_SLEEP_LOCK_FD` plus an open fd) = `displayed@1s=0`, i3lock at
    t1s (suspend never delayed). Every path restored pause 0 and removed
    the pause file. Method note: `flameshot full -p` silently refuses to
    overwrite an existing file: `rm -f` the target first, or pixel
    diffs compare stale images.
11. **Sweep items (b), (c), (h): bar signals, dead bindings:**
    `custom/updates` and `custom/dnd` polled on blind timers, so
    topgrade completion left the count stale up to 600s and the DND
    toggle up to 5s. polybar splits the remedy across module types
    (`custom/ipc` has actions but no interval, `custom/script` has
    `interval` but no action), so `custom/dnd` became `custom/ipc`
    (`initial = 1`; `--toggle` ends with `polybar-msg action custom/dnd
    hook 0`) while `custom/updates` became a `tail = true` loop
    carrying both the 600s refresh and a `SIGUSR1` trap that
    `toggle_topgrade.sh` fires from the kitty wrapper once topgrade
    exits (`pkill -USR1 -f` anchored on the script's exact cmdline).
    `dunst-dnd.sh` reads an empty `dunstctl` level as off, since
    `custom/ipc` has no interval to heal a stale first read. (h)
    removed the `XF86MonBrightness*` bindings: optiplex has no
    `/sys/class/backlight` device. `brightnessctl` stays in the shared
    package list for thinkpad's sway bindings. Live-verified: the icon
    flips on toggle and round-trips pixel-identical (pause 50 → 0),
    the anchored poke re-reports within seconds, two
    `polybar-msg cmd restart`s leave exactly one tail instance, and a
    shadowed `i3-msg`/`kitty` pass delivers the poke command intact
    without running topgrade.
12. **Sweep items (a), (d), (e), (f): `sw` on feh, clipboard parity,
    title rewrites, MPRIS grace:** (a) `sw` selects a wallpaper backend
    with `wallpaper_backend()`: awww first (Wayland/thinkpad), feh on
    X11/optiplex. `ensure_backend()` replaces the three
    `awww_running()` gates: rotation dies only when awww is chosen with
    a dead daemon (feh is stateless). feh runs `--no-fehbg`; `sw` alone
    writes `~/.fehbg` (its comment, a `$HOME`-relative path, mode 755)
    for i3's `exec ~/.fehbg`, and chezmoi dropped that file (source +
    ignore line) once a sw-written file turned apply into a TTY
    prompt. `lutgen-cli-git` joined the optiplex package list (stills
    need it; the gif path does not). Live: `--set`/`--next`/
    `--restore` exit 0 on the pool gif, `~/.fehbg` keeps sw's form and
    `sh ~/.fehbg` runs, `chezmoi apply` stays silent with sw's file,
    and where pre-fix `sw --restore` died with "awww daemon is not
    responding" it now reaches the real "no previous wallpaper
    recorded" error. (d) `-c` landed on all three bindings:
    `flameshot full -p … -c` wrote both the file and an identical
    260348-byte PNG through `xclip -t image/png`, and both scripts
    pass `-c` to `flameshot gui` (their confirm/cancel legs rest on
    the documented flag, paste-test pending). (e) `custom/window`
    replaced `xwindow` with a 1s `xdotool` poll (`xprop` is absent)
    carrying waybar's `rewrite` table and 72-column cap; verified
    against a shadow xdotool table (` - Helium` stripped,
    `• Discord | general` → `general`, `nvim …` → ` Editing …`, empty
    → one space) and live in the bar center ("OC | Continue work from
    HANDOFF.md"). (f) `executable_mpris.py` ports waybar's engine
    whole (follow + resync, hide-after-grace, cache, stall) with
    polybar tags; `custom/mpris` switched `interval = 5` →
    `tail = true`, the twin suite reuses waybar's `fake_playerctl.py`
    instead of duplicating it (7 scenarios PASS), and
    `make check-mpris` now type-checks and runs both scripts' suites.

### Updates-click and edge-borders round: 2026-09-27 (optiplex)

Two reported issues; both fixed, applied, and verified:

1. **Reported: clicking the updates module spawned no terminal and
   the cursor hung in the loading state.** The spawn line was
   `i3-msg exec "kitty … -e sh -c 'topgrade; pkill …'"`, and i3's
   grammar only quotes with `"`: a bare `;` inside `'…'` still ends
   the command (live repro: i3 executed only the truncated
   `exec kitty … -e sh -c 'topgrade` and rejected the rest, so
   i3-msg exited 2). The shell i3 starts therefore dies on the
   unmatched quote before kitty runs (no window), and the toggle's
   `set -e` dies before `release_sway_lock`, leaving a dead-PID lock
   per click (21:20 and 21:34; the stale takeover kept later clicks
   going). The truncated exec had already opened a
   startup-notification, so `refs/src/i3/src/startup.c` armed
   `XCURSOR_CURSOR_WATCH`, gated only by `!no_startup_id` (line
   211), for a window that never appears: the stuck loading cursor,
   re-armed by every click. The earlier "shadowed i3-msg/kitty pass"
   (item 11) proved only the script's argument; the stub never ran
   i3's parser. Fix: `topgrade; pkill …` moved to
   `i3/scripts/wrapper_topgrade.sh` (topgrade guarded by `|| true`
   so a failing run still pokes, as the old non-`set -e` inner sh
   did), spawned as
   `i3-msg "exec --no-startup-id kitty --name $app_id -e …/wrapper_topgrade.sh"`:
   nothing left for i3 to split, and the flag must ride inside the
   single i3-msg argument: passed standalone, i3-msg's own option
   parser rejects it with `unrecognized option` (reproduced). With
   `--no-startup-id` no startup-notification exists to wedge. The
   sway twin needs no change: sway(5) COMMAND CONVENTIONS quotes
   with `'…'` as well as `"…"` (its `;` is protected) and sway's
   `exec` has no startup-id mechanism. Verified: `sh -n`,
   `i3 -C -c ~/.config/i3/config`, `i3-msg reload`; the spawn branch
   run against a stand-in wrapper (only the `-e` path swapped): parse
   success, `topgrade_term` mark applied, show/hide round-trip, no lock
   left. Poke chain live (wrapper → SIGUSR1 → updates.sh re-reported
   within the same second). The real click starts a real topgrade: item
   13's hand-test.
2. **Reported: keep borders with a single window in the workspace.**
   `hide_edge_borders smart` → `none` in `i3/config.tmpl` and
   `sway/config.tmpl`: `smart` "hides borders on workspaces with
   only one window visible" (`refs/i3/userguide.html`), and in
   sway(5) `smart` equals `smart_borders smart`, while `none` is
   both WMs' documented default of never hiding edge borders.
   Optiplex verified: `i3 -C` + reload, `i3-msg -t get_config` reads
   `hide_edge_borders none`, and a pixel probe of a
   `flameshot full` capture shows the `#5A5A5A` focused 1px border
   on all four edges of the lone kitty window (rect x=8, y=32,
   1350×728 → border pixels at x=8, y=32, x=1357, y=759). The sway
   half lands with the next thinkpad apply (no sway binary here;
   `none` confirmed in `refs/sway/sway.5.scd`).
