# Background services

This page covers the programs that run without a window.

## The session groups

Logging in starts the desktop services together, and logging out stops them:

- **thinkpad** uses `sway-session.target`; **optiplex** uses
  `i3-session.target`.
- The session autostart script starts the target at login, and the units it
  pulls in are listed in the matching `*-session.target.wants` directory under
  `home/dot_config/systemd/user/`. Removing a symlink disables the unit for the
  next session; adding one starts it.

Work with the units through systemd as usual:

```sh
systemctl --user status wlsunset
journalctl --user -u calibre-sync
```

The per-machine unit inventory is in [FEATURES.md](../FEATURES.md).

## Power shortcuts

`$mod+Shift+Backspace` powers off, `$mod+Shift+r` reboots, and `$mod+Shift+e`
logs out. Each asks for a yes/no confirmation first — see [Pickers](pickers.md)
for how the prompt behaves.

## The idle path

The idle timer belongs to
[Screenshots, lock, and idle](screenshots-lock-idle.md): swayidle units on
thinkpad, `xset` plus `xss-lock` on optiplex. optiplex has no idle units and
never suspends on its own.

## Night light

- **thinkpad** runs `wlsunset`; the `wlsunset-location` helper sets the
  coordinates if it picks the wrong ones.
- **optiplex** runs `redshift`.

## Recurring jobs

- **`chezmoi-drift.timer`** runs `chezmoi-drift-check` daily. It stays silent
  while everything matches and notifies when the deployed dotfiles drift from
  the source or unmanaged files appear.
- **`calibre-sync.timer`** syncs the Calibre library every 30 minutes, and
  `calibre-sync-netmon.service` re-arms it after the network comes back. The
  sync needs an rclone `gdrive` remote; `journalctl --user -u calibre-sync`
  shows what it did.

## Background daemons

- **Syncthing** runs on both machines from `default.target`, not the session
  target, so it survives a logout.
- **The policy agent** (`polkit-agent.service`) authenticates privileged actions
  for the session.
- **The wallpaper daemon** (`awww-daemon.service`) holds the current wallpaper
  on thinkpad; optiplex uses feh instead. The tray applets are started at
  session start by the bar hook rather than by units.
