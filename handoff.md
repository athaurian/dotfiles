# Handoff: dotfiles reset

## What happened

The old repo (~200 tracked files) collapsed under its own tooling: a
Flint/Sand palette system (`flint_palette.py`, palette YAMLs, a build
script, WCAG checks), 45 templates fed by it, a Sway session manager
library, a picker library, lint/format gates per filetype, docs with an
enforced style guide, and wallpaper recoloring. Changes got expensive,
nothing useful shipped, fatigue set in.

We archived the working tree to `~/Documents/archive/dotfiles-backup.zip`
(plus a HEAD-only zip and a `config-managed-backup-*.tar.gz` of the live
`~/.config` targets), wiped every previously managed file under
`~/.config` back to app defaults, emptied the repo to just `.git/`, and
are rebuilding it file by file from git history (`HEAD`, pre-reset).

## Where the repo stands now

Small, static, no templating except where chezmoi needs it (a `symlink_`
unit and the shell aliases file). Current source tree:

- `.chezmoiroot` — source root is `home/`.
- Sway: `home/dot_config/sway/config` — minimal keybinds (vim
  focus/move, workspaces, layout, scratchpad, resize mode), trackpad
  block, floating rules for pavucontrol/blueman-manager, `Mod+Shift+v/b`
  launchers, Geist Mono font, `bar { swaybar_command waybar }`.
- Terminal/launcher: `foot.ini` (GeistMono Nerd Font Mono), `fuzzel.ini`
  (same font, Papirus-Dark icons).
- Bar: `waybar/config.jsonc` + `style.css` — six stock modules
  (workspaces, mode, window, cpu, memory, pulseaudio, battery, tray,
  clock) with Nerd Font icons and the original margin/padding rhythm. No
  `custom/*` modules (their scripts are gone). Colors are a temporary
  neutral dark `tmp-*` palette, all 17 variables referenced.
- Notifications: `dunst/dunstrc` — layout and DND bypass levels kept,
  stock colors.
- Shell: `dot_bashrc`, `dot_bash_profile`, `dot_bash_aliases.tmpl`
  restored verbatim.
- Editor: minimal LazyVim (`init.lua`, `lua/config/lazy.lua`,
  `lua/plugins/colorscheme.lua` pinned to stock `tokyonight`,
  `lazyvim.json`, `stylua.toml`, `.neoconf.json`). Dropped the Flint
  catppuccin overrides, cord, custom dashboard, persistence handshake,
  and snacks tweaks.
- Night light: standalone `wlsunset` pipeline
  (`wlsunset-location` script, `wlsunset-env.service`,
  `wlsunset.service` on `default.target`, autostarted via
  `default.target.wants/symlink_wlsunset.service.tmpl`).
- GTK: static dark defaults (`Orchis-Dark-Compact`, `Papirus-Dark`,
  Geist 10, Adwaita cursor) in `dot_gtkrc-2.0` and both settings files,
  plus file-manager bookmarks.
- Git identity/aliases: `dot_config/git/config` restored verbatim.
- Launchers: four `.desktop` entries (btop, nvim, KeePassXC with the
  qt5ct pin, zellij).

## Rules going forward

1. Defaults first. Live with stock app behavior for days before adding
   config. Add only on real friction, never preemptively.
2. No palette builder. No `.tmpl` color variables, no `palettes/`, no
   contrast gates, no wallpaper recoloring. If a scheme is ever wanted,
   paste static hex into the two or three files that need it.
3. No new libraries or gates. No `session_manager_lib`, no
   `picker_lib`, no per-filetype lint targets, no docs style checker.
   Shell one-liners over Python packages; `swaymsg`/`systemctl` over
   wrappers.
4. Cherry-pick from history, don't bulk-restore. `git show
   HEAD:<path>` to inspect, restore single files, then strip them to
   static minimal form before applying.
5. Keep commits small and tell the truth in them. Tag anything that
   works (`minimal-baseline`) so rollback is one command.

## Immediate next candidates (only if missed)

- `btop` / `lazygit` / `zathura` static configs, stripped of Flint vars.
- `swaylock` minimal config (was fully themed; needs a plain rewrite).
- Decide the real color story: keep the temporary `tmp-*` Waybar palette
  and stock everything-else, or pick one upstream static theme and paste
  it in. Do not rebuild the generator either way.
