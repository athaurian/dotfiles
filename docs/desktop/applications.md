# Applications

Most application files in `home/dot_config/` are generated or templated from
`meta/palette.toml`. Rather than listing every setting in those files, this page
covers the non-obvious hooks, notification rules, and font priorities.

## Theme synchronization hook (`run_onchange_after_gtk-mode-hook.sh.tmpl`)

When `chezmoi apply` runs after a dark/light switch, a post-apply hook updates
applications that store their theme state outside plain dotfiles:

- **GTK / GSettings**: Updates `color-scheme` (`prefer-dark` vs `prefer-light`)
  and GTK icon/theme keys for running GTK3/GTK4 apps.
- **Calibre**: Rewrites Calibre's UI palette config **only when Calibre is not
  running**, because Calibre overwrites its configuration files on exit and
  would clobber external edits made while a window is open.

## Notifications and Do Not Disturb (`dunst`)

Toggling Do Not Disturb from the status bar sets `dunst`'s pause level to `50`,
silencing normal notifications while still allowing critical system alerts
through.

In `dunstrc`, six notification sources are assigned an override rule with
`override_pause_level = 90` so they bypass DND:

- `dunst-dnd` (Do Not Disturb toggles)
- `caffeine-toggle` (idle-inhibitor toggles)
- `sw` (wallpaper errors)
- `idle-warning` (idle timeout warnings)
- `lock` (screen-lock and session actions)
- `screenshot` (capture results and failures)

## Font priorities (`fonts.conf`)

- **Serif**: Adds **Merriweather** as a weak `serif` preference. The weak
  binding leaves the system language-specific serif mappings in place for
  scripts Merriweather does not cover, such as CJK.
- **Code**: Prefers **GeistMono Nerd Font Mono** for glyphs missing from **Geist
  Mono**, without replacing the requested family.
- **GTK applications**: Use **Geist** for UI text and **Geist Mono** for
  monospace text.

## Other configured tools

- **Document viewer (`zathura`)**: Recolors PDF pages to match the active dark
  or light palette by default; toggle original document colors at any time with
  `Ctrl+r`.
- **Terminal stack (`kitty` + `zellij`)**: Configured with palette includes so
  `make dark` / `make light` reloads terminal colors live via `kitty` remote
  control signals.
- **Vesktop (Discord)**: Pulls a generated QuickCSS theme file mapped from
  `meta/palette.toml`.
