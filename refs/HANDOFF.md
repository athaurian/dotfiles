# Session handoff: read this first

Written 2026-09-24 from a `thinkpad` session. **The next session runs on
`optiplex`.** You inherit no conversation context; everything you need is
here and in `refs/polybar-migration-findings.md` (the deep, source-verified
ledger: this file is the map, that file is the proof).

## The setup

- Chezmoi Linux desktop config repo (`github.com/athaurian/dotfiles`,
  branch `main`). `.chezmoiroot` = `home`, so `home/dot_config/x` deploys to
  `~/.config/x`.
- **Two machines, one repo.** `thinkpad` = Sway/Wayland + waybar + fuzzel +
  SwayFX shadows. `optiplex` = i3/X11 + polybar + rofi + picom + dunst.
  Per-machine split lives in `home/.chezmoiignore` (optiplex block line 13,
  thinkpad block line 27) and `data/packages.json` (`machines` → onboarding
  picks the list by hostname). Consequence: on thinkpad, `chezmoi diff` never
  shows rofi/i3/picom/polybar files (ignored), and on optiplex it never shows
  waybar/sway/fuzzel files. Files landing on both machines (dunst,
  dunst-dnd, systemd units) either branch with
  `{{ if eq .chezmoi.hostname "optiplex" }}` (of those, only
  `polkit-agent.service.tmpl` and `dunstrc.tmpl` branch) or ship
  per-machine copies (`dunst-dnd` differs between `waybar/scripts/` and
  `polybar/scripts/`).
- Working rules: **`AGENTS.md`**: verify before changing, smallest necessary
  change, palette changes go `meta/color-scheme.md` → `make palette` →
  consumers, verification table at the bottom (`make lint`, `chezmoi diff`,
  `i3 -C -c ~/.config/i3/config`, `sway … --validate`).

## Why this handoff exists

Verification is the bottleneck: **i3, i3-msg, polybar, polybar-msg, rofi and
picom binaries do not exist on thinkpad**, so every runtime/visual check of
the optiplex port has been deferred session after session. All such checks
are now queued below and in the findings doc's checklist. Do the optiplex
checks **before** starting new edit work.

## Git state

`main` is pushed; confirm the tip with `git status -sb`. No HEAD SHA is
pinned here: a SHA written into a committed document is stale as soon as
this file changes. Recent history:

- `e505702`: polybar spacing/clicks match waybar; waybar made thinkpad-only.
- `598b40d`: port audit: `$mod+Shift+c` reload chain restarts polybar,
  `--release` on three toggle bindings, `[module/i3mode]` resize chip,
  `lock.sh --now` xss-lock fd contract, `xss-lock`+`xorg-xset` packages.
- `891066c`: this round's five visual-parity fixes (below).
- `963bf36`: `refs/` un-ignored and committed with reproducible material
  pruned behind `fetch-refs.sh`.
- `ee7892a`: `fetch-refs.sh` extended to every repo-owned doc surface;
  `refs/.gitignore` added.
- `9d2bf4f`: this file's stale claims corrected (Git state, script
  pointers, pin exception, dunst-dnd framing, dunst filenames).

`backup/pre-reset-2567b2d` is a **local-only** branch (not pushed; absent on
`optiplex`, whose `main` already contains `2567b2d`); it is historical
reference material, per AGENTS.md not an architecture to restore.

## This round's fixes (all applied and thinkpad-validated)

User feedback verbatim: rofi glyph→input spacing too far, rofi padding must
match fuzzel exactly, picom shadows bottom-right instead of centered,
power-control prompts show "find something..." where "Enter=yes, Esc=no"
belongs, dunst overlaps the bar on optiplex (thinkpad sits below it), and the
"Muted" text should be dimmed. Clarifications: **only thinkpad lacked the
dimmed Muted** (polybar already dims via `label-muted-foreground`); scope =
only the reported items.

1. **Rofi padding/spacing**: `home/dot_config/rofi/config.rasi.tmpl`
   (optiplex-only). `window padding` `8px` → `8px 16px` to mirror fuzzel's
   `horizontal-pad=16` / `vertical-pad=8`; `inputbar spacing` `8px` → `2px`
   (the prompt already carries a trailing space, so 8px read as double).
   `inputbar padding-bottom` stays 8px = fuzzel `inner-pad=8`. Multi-value
   padding is CSS-style, verified in `refs/rofi/rofi-theme.5.markdown`
   (restorable via fetch script).
   **Verify (optiplex):** `$mod+d`: search glyph hugs the input text, box
   inset 16px left/right, 8px top/bottom; compare against fuzzel memory or a
   thinkpad screenshot.
2. **Power-confirm hint**: `home/dot_config/i3/scripts/executable_power_control.sh`,
   `confirm_menu()`: the theme never renders a `message` widget, so `-mesg`
   showed nothing and only the input placeholder ("find something...") was
   visible. The hint now rides in the entry placeholder via
   `-theme-str "entry { placeholder: \"$confirm_placeholder\"; }"` (fuzzel
   passes the same string as `--placeholder`). Launcher placeholder is
   untouched. **Verify (optiplex):** `$mod+Shift+z` → prompt
   `confirm suspend? `, grey `Enter=yes, Esc=no` **inside the input box**.
   Esc/arrow-cancel works. Do **not** press Enter unless you want to suspend.
3. **Dunst below the bar**: `home/dot_config/dunst/dunstrc.tmpl`
   (deploys on both machines). Wayland dunst is pushed below waybar's 24px
   exclusive zone before its `(8, 8)` offset applies (→ top at y=32); X11
   dunst measures from the screen edge with no strut awareness, so it
   overlapped the 24px polybar. Offset is now
   `(8, {{…optiplex}}32{{…else}}8{{end}})`: optiplex renders `(8, 32)`,
   identical geometry to thinkpad; thinkpad stays `(8, 8)`. **Verify
   (optiplex):** `systemctl --user restart dunst` (or `pkill dunst`;
   dbus-activation relaunches it), then
   `notify-send "geometry" "below the bar"` → 8px from right edge, top edge
   8px below the 24px bar. Also `grep offset ~/.config/dunst/dunstrc` after
   apply → must read `(8, 32)`.
4. **Waybar muted dim** (thinkpad-side) in `home/dot_config/waybar/style.css.tmpl`:
   new `#pulseaudio.muted { color: @neutral-text-muted; }`, deliberately
   placed **after** `#pulseaudio:hover` so hovering does not un-dim it
   (polybar has no hover state; equal specificity → later rule wins).
   Selector confirmed against the waybar wiki (STYLE lists
   `#pulseaudio.muted`). **Verify (thinkpad, when back):** reload waybar,
   `pactl set-sink-mute @DEFAULT_SINK@ toggle` → `󰖁 Muted` renders grey,
   stays grey on hover; toggle back.
5. **Picom shadows: diagnosed; config stays `(0, 2)` (report only).**
   The stale-instance hypothesis is rejected: the running process is
   `picom --config ~/.config/picom.conf` (single instance; config mtime
   predates it), applies `shadow-opacity 0.5`, and honors the offset keys
   (`60,60` extends the right reach to +83px). The bottom-right look is a
   renderer limitation of the installed build (`picom v13 git rev
   d87a5ba`): shadow tails render only where the shadow core reaches the
   window edge, so right/bottom need offset ≥ 0 while left/top need ≥ ~14px
   protrusion, so no offset yields a four-sided shadow. **Outcome:** keep
   `(0, 2)` (the thinkpad-mirror intent) and report the limitation; full
   measurement matrix in the findings doc's "Verification results".

## Carried verification checklist (from `refs/polybar-migration-findings.md`)

Run these on optiplex after `git pull && chezmoi apply` (the findings doc has
full wording and the source proofs behind each item):

1. `i3 -C -c ~/.config/i3/config` parses (reload chain, `border normal`
   rules, `--release` bindings).
2. `$mod+Shift+c` after a polybar edit restarts polybar, no duplicate bars.
3. `$mod+r` resize chip appears bold yellow-on-`warning-hover`, and the bar
   is pixel-identical at rest afterwards.
4. Hold-key test: DND / caffeine / drop-term toggle exactly once
   (`--release` behavior).
5. Drop-term and topgrade scratchpads float **with a titlebar**.
6. Three suspend paths lock before sleep (power menu, `systemctl suspend`,
   `xset s 20 10` idle: warns at 20s, locks at 30s); DND restores on wake.
7. Print / Shift+Print / Ctrl+Print save into `~/Pictures/Screenshots`
   (auto-created at startup); region capture works.
8. Logout stops `calibre-sync-netmon` (bound to `i3-session.target`).
9. Next apply re-runs onboarding (packages.json hash) and reports
   `lutgen-cli-git` as new: what the `sw` feh backend needs for
   stills on optiplex; by design.
10. `polybar -vvv` includes the i3 module build flag.
11. **New:** the five fixes above (rofi layout, confirm placeholder, dunst
    geometry, picom cmdline, and the thinkpad waybar muted check).
12. **New:** `$mod+Shift+space` restores a shown scratchpad window to the
    current workspace (tiled, default border) and plain-float-toggles
    other windows; an idle session gets the `screen locking in 10s`
    warning at 20s that cancels the 30s lock if you move, then the
    `locking screen...` beat for 2.5s as the lock begins.
13. **New:** DND flips the indicator the instant `$mod+Shift+d` (or a
    click) toggles it (no 5s lag), and after a topgrade run the
    updates count refreshes as soon as topgrade exits instead of up to
    600s later.
14. **New:** the four sweep fixes: Shift+Print/Ctrl+Print captures
    reach the clipboard (`-c` on both; the interactive confirm/cancel
    legs are docs-based), `sw --next`/`--set`/`--restore` rotate the
    pool through feh and keep `~/.fehbg` in step for the next login,
    the bar center shows the active window title with waybar's
    rewrite rules, and a playing player's module hides after the
    grace pause and returns on resume.

Status (2026-09-27): **all checklist items verified.** 8 confirmed by
real logouts: the journal shows calibre-sync-netmon and
i3-session.target stopping in the same second on two logouts
(13:10:59, 13:11:53), the unit restarting on each login. 12, 13, and
14 hand-tested by the user. Thinkpad verified the deferred sweep: the
`$mod+d` hold test, the toggle_floating port, screenshot clipboard
parity, and the dunst shadow look. The sweep itself: toggle_floating
ported to sway (leaf check accepts app_id; Wayland windows carry no
X11 id), screenshot `-c` parity via wl-copy, cliphist and the dead
`clipboard_term` exclusion dropped, the topgrade poke kept inline,
lock.sh quirks accepted. The calibre sync units are now
optiplex-ignored: optiplex's library differs from thinkpad's and has
no rclone config, so the gdrive mirror never ran there (every run
failed since the unit was created); thinkpad keeps the units.
Records still standing from earlier rounds: 6 by real suspend cycles,
7 re-verified after the flameshot rewrite, dunst's 1.0625× DPI offset
deviation reported not compensated, picom shadows kept at `(0, 2)`
(renderer limitation, reported). Full evidence in the findings doc's
"Verification results" and "Acceptance round".

## `refs/` layout (COMMITTED; restored material ignored by `refs/.gitignore`)

- **Committed:** `polybar-migration-findings.md` (authoritative verified
  ledger + round-2 findings), this handoff, `fetch-refs.sh`, `.gitignore`,
  `zellij-themes/` (5 `.kdl` files whose upstream source could not be
  located, so they are kept rather than scripted).
- **Everything else is restored** with `sh refs/fetch-refs.sh [target-dir]`
  (default target = `refs/` itself; `refs/.gitignore` keeps restored files
  out of `git status`; verified end-to-end on thinkpad: full run into a
  temp dir, pins match, idempotent re-run). Every clone, source tree, and
  doc fetch is pinned to a specific commit: the sole exception is the
  rendered `i3/userguide.html`, which tracks the latest i3 release (its
  asciidoc source is pinned under `refs/src/i3/docs/userguide`). The
  script covers:
  - clones: the 5 nvim-theme/plugin repos, `polybar-wiki`, `waybar-wiki`
    (the bar-migration source of truth), and `chezmoi` (reference docs under
    `assets/chezmoi.io/docs/`);
  - full source trees: `refs/src/i3/` and `refs/src/polybar/`, the exact
    commits whose files the findings doc cites as proof (`refs/i3/*.man`
    and `refs/polybar/*.rst` are copied from them by the script);
  - man/doc fetches, one directory per tool: `sway/` (7 scds incl. swaymsg),
    `swayfx/`, `swaylock/`, `swaylock-effects/` (jirutka, the fork Arch
    ships), `swayidle/`, `fuzzel/`, `foot/`, `grim/`, `slurp/`, `satty/`,
    `awww/` (9 scds), `wlsunset/`, `rofi/` (5 files incl. rofi-script),
    `picom/` (sample conf + man adoc), `dunst/` (`dunst.1.pod.in`,
    `dunst.5.pod` = the config reference, `dunstctl.pod`, `dunstify.pod`),
    `i3/`, `i3lock-color/`, `redshift/`, `xss-lock/` (fd-contract man +
    transfer script; freedesktop GitLab is auth-walled, so a GitHub mirror
    is used), `feh/`, `flameshot/`, `kitty/`, `zathura/`, `btop/`, `cava/`,
    `fastfetch/` (man + json_schema), `lazygit/`, `topgrade/`,
    `playerctl/`, `systemd/` (unit/service/exec/timer/special XML for the
    user units);
  - `dotfiles-pre-reset.bundle` (67M, regenerated locally from the
    identical `backup/pre-reset-2567b2d` ref, so the bytes do not belong
    in git).
- **Deliberately not fetched** (nothing in the repo needs them): `zellij`
  (`config.kdl` is 16 bytes + committed themes; `zellij setup --dump-config`
  regenerates the reference), `lutgen` (fully documented in
  `meta/lut-palette.md`), `cliphist` (installed but referenced nowhere in
  the repo), `qt5ct` (upstream GitLab not fetchable anonymously; the config
  is self-evident and GUI-configurable), GTK `settings.ini`/`.gtkrc-2.0`
  (keys self-evident, no pinned raw source), `git`/`bash` config (man pages
  on both machines; git.git upstream docs are a fragmented tree), `calibre`
  (calibredb man ships with the package; repo scripts have their own
  tests), and apps with no repo-managed config (mpv, blueman, nm-applet,
  pavucontrol, thunar, keepassxc, syncthing, networkmanager) or unmanaged
  paths (ly's `/etc/ly` per AGENTS).

## Deferred by user decision ("only what I reported" this round)

- dunst shadow strength vs thinkpad: looked at on thinkpad, accepted
  (2026-09-27).
- `cliphist`: dropped with the dead `clipboard_term` exclusion
  (2026-09-27).
- no `--locked` media keys on optiplex, flameshot vs grim/satty,
  xss-lock/xset vs swayidle, feh vs awww, redshift vs wlsunset,
  touchpad block, waybar tooltips: all platform-justified, accepted
  earlier.

## Operating notes for this session

- Order: `git pull` → read findings doc tail (checklist) → run checklist +
  this round's verifications → only then edit further.
- Config read timing: rofi reads config per launch (no restart). Dunst and
  picom need a restart. Polybar restarts via `$mod+Shift+c`. Waybar reloads
  only on thinkpad.
- `chezmoi diff` before `chezmoi apply` on optiplex; expect onboarding
  re-run if the packages hash is newer than its recorded state.
- Validation available on optiplex that thinkpad lacked: `i3 -C`,
  `polybar -vvv`, `rofi -dump-config`, picom cmdline inspection: use them,
  they are exactly the checks that were impossible before.
