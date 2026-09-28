# Features

An index of everything this repository configures: keybinds, background
services, bar modules, scripts, and tooling, each pointing at the source that
stays authoritative. Keep entries feature-level — what exists and where it lives
— rather than copying config contents.

Two machines: **thinkpad** (Sway, Wayland) and **optiplex** (i3, X11).
`.chezmoiignore` splits the per-machine file sets, and `data/packages.json`
holds the per-machine package lists. See `AGENTS.md` for operating rules.

## Sessions and desktop

| Feature                                                                           | Machine  | Source                                                                                                                  |
| --------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| Display manager `ly` starts the graphical session                                 | both     | `/etc/ly/config.ini` (unmanaged); session log `~/.local/state/ly-session.log`                                           |
| Sway configuration                                                                | thinkpad | `home/dot_config/sway/config.tmpl`                                                                                      |
| i3 configuration                                                                  | optiplex | `home/dot_config/i3/config.tmpl`                                                                                        |
| Session bootstrap: imports compositor env into systemd, starts the session target | both     | `home/dot_config/{sway,i3}/scripts/executable_autostart.sh`                                                             |
| Bar                                                                               | thinkpad | Waybar, started by `bar { swaybar_command waybar }`; `home/dot_config/waybar/`                                          |
| Bar                                                                               | optiplex | Polybar, started by i3 `autostart.sh` (`polybar main`); `home/dot_config/polybar/`                                      |
| Tray applets (blueman, network manager)                                           | both     | `exec_always` in both configs (i3 runs `i3/scripts/applets.sh`); the gtk-mode hook restarts them for the new icon theme |
| picom compositor, feh wallpaper at login                                          | optiplex | `home/dot_config/i3/config.tmpl`                                                                                        |

## Keybinds

The full lists live in the two configs; stock window, workspace, and layout
binds are not repeated here. The script-backed and distinctive bindings, all
identical across machines unless noted:

| Keys                               | Action                                                                                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$mod+Return`                      | Terminal (foot on thinkpad, kitty on optiplex)                                                                                                      |
| `$mod+d`                           | App launcher (fuzzel on thinkpad, rofi on optiplex)                                                                                                 |
| `$mod+Shift+t`                     | Toggle light/dark mode → `palette-mode toggle`                                                                                                      |
| `$mod+Shift+i`                     | Caffeine mode: toggle swayidle → `scripts/toggle_idle.sh`                                                                                           |
| `$mod+Shift+d`                     | Toggle DND → bar's `dunst-dnd.sh --toggle`                                                                                                          |
| `$mod+n` / `$mod+Shift+n`          | Close / close-all notification (dunstctl)                                                                                                           |
| `$mod+Shift+x`                     | Lock screen → `scripts/lock.sh`                                                                                                                     |
| `$mod+Shift+BackSpace/r/z/e`       | Poweroff / reboot / suspend / logout → `scripts/power_control.sh` (with confirmation)                                                               |
| `$mod+minus` / `$mod+grave`        | Cycle scratchpad / dropdown terminal                                                                                                                |
| `$mod+Shift+space`                 | Toggle floating                                                                                                                                     |
| Screenshots                        | thinkpad: `Print` full / `Shift+Print` region (`screenshot.sh`); optiplex: `Print` flameshot full, `Ctrl+Print` window, `Shift+Print` flameshot GUI |
| Media keys                         | Volume and playback (pactl/playerctl); brightness (brightnessctl, thinkpad only) — sway binds are `--locked` so they work at the lock screen        |
| `$mod+b/e/Shift+p/Shift+v/Shift+b` | Browser, file manager (thunar), password manager (keepassxc), pavucontrol, blueman-manager                                                          |
| `$mod+Shift+c`                     | _optiplex only:_ reload i3 and restart polybar                                                                                                      |

## Background services and timers

Enabled through the systemd user session targets the autostart scripts start;
the wants lists are
`home/dot_config/systemd/user/{sway,i3}-session.target.wants/`.

| Unit                          | Session      | What it does                                                                                                        |
| ----------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------- |
| `swayidle-unlocked.service`   | sway         | Idle timeouts via `wrapper_swayidle.sh unlocked`                                                                    |
| `swayidle-locked.service`     | by `lock.sh` | Idle behavior while locked; lock state coordinates both swayidle units — changes must follow `lock.sh` control flow |
| `awww-daemon.service`         | sway         | Wallpaper daemon                                                                                                    |
| `wlsunset.service`            | sway         | Night-light gamma                                                                                                   |
| `redshift.service`            | i3           | Night-light (X11)                                                                                                   |
| `calibre-sync.timer`          | sway         | Runs `calibre-drive-sync` every 30 minutes                                                                          |
| `calibre-sync-netmon.service` | sway         | Debounced sync soon after Wi-Fi reconnect (timer stays fallback)                                                    |
| `chezmoi-drift.timer`         | sway, i3     | Daily `~/.local/bin/chezmoi-drift-check`                                                                            |
| `polkit-agent.service`        | sway, i3     | Authentication agent                                                                                                |
| `syncthing.service`           | default      | File sync                                                                                                           |

optiplex has no idle units: its idle path is native X11 (`xset s`, `xset dpms`,
`xss-lock` with `idle_notifier.sh` and `lock.sh` from the i3 config), and it has
no idle suspend.

## Bar modules

Shared between Waybar (`home/dot_config/waybar/config.jsonc`) and Polybar
(`home/dot_config/polybar/config.ini.tmpl`); each module's script lives under
the bar's `scripts/` directory.

| Module           | Script                      | What it does                                                                                           |
| ---------------- | --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `custom/mpris`   | `mpris.py`                  | Media player control and track display (`make check-mpris`)                                            |
| `custom/updates` | `updates.sh`                | Counts pending pacman/AUR updates; click runs `toggle_topgrade.sh` (upgrades in a scratchpad terminal) |
| `custom/dnd`     | `dunst-dnd.sh`              | DND toggle (same action as `$mod+Shift+d`)                                                             |
| `custom/window`  | `window_title.py` (polybar) | Focused window title                                                                                   |

## Palette mode and wallpaper

| Feature               | Source                                                                                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Mode switch           | `make light` / `make dark`: records the mode, regenerates palette data, applies it (GTK via `home/.chezmoiscripts/run_onchange_after_gtk-mode-hook.sh.tmpl`)                   |
| Toggle CLI            | `palette-mode [dark\|light\|toggle]` — flock-guarded, notifies through dunstify; `home/dot_local/bin/executable_palette-mode`                                                  |
| Color source of truth | `meta/color-scheme.md` → `make palette` (`meta/palette.py`) → LUTs documented in `meta/lut-palette.md`                                                                         |
| Wallpaper             | `sw` — set/list/restore with per-mode restore; sway runs `sw --restore` at login, optiplex restores `~/.fehbg` through feh (`--no-fehbg`). `~/.fehbg` is written only by `sw`. |

## Repo tooling

Lives at the checkout root `~/.local/share/chezmoi` (not the `home/` source root
— see `AGENTS.md`).

| Target / tool               | What it does                                                                |
| --------------------------- | --------------------------------------------------------------------------- |
| `make palette`              | Regenerate derived palette data from `meta/color-scheme.md`                 |
| `make light` / `make dark`  | Switch palette mode                                                         |
| `make lint` / `make format` | Check / format repository markdown                                          |
| `make check-mpris`          | Ruff, mypy, and tests for the bar MPRIS scripts                             |
| `make check-sw`             | Checks for the wallpaper helper                                             |
| `make check-refs`           | Probe every pinned `refs/` URL for bitrot (network)                         |
| `make check-config`         | Validate the applied configs with each program's own checker                |
| `chezmoi-drift-check`       | Reports repository drift; run daily by `chezmoi-drift.timer`                |
| `meta/probe*.lua`           | Headless Neovim checks: palette, Mason/Lazy pill chrome, dim-float backdrop |

## Standalone tools (`~/.local/bin`)

| Tool                                         | What it does                                                                                                    |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `sw`                                         | Wallpaper: set, list, restore (per-mode records)                                                                |
| `palette-mode`                               | Print, set, or toggle the palette mode                                                                          |
| `chezmoi-drift-check`                        | Notify when deployed dotfiles drift from the source or unmanaged files appear                                   |
| `calibre-drive-sync` / `calibre-sync-netmon` | Mirrors the Calibre library to Google Drive via rclone — by timer, manually, or debounced after Wi-Fi reconnect |
| `wlsunset-location`                          | Location helper for wlsunset                                                                                    |

Machine-specific helpers live in `home/dot_config/sway/scripts/` (thinkpad) and
`home/dot_config/i3/scripts/` (optiplex); each bar's scripts live under
`home/dot_config/{waybar,polybar}/scripts/`.
