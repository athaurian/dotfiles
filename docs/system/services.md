# Services

Background daemons are managed as `systemd` user units under
`home/dot_config/systemd/user/` rather than bare `exec` lines in the window
manager config, so crashes restart cleanly and logs stay queryable in
`journalctl --user`.

## Design choices

- **Non-blocking compositor startup (`systemctl --user start --no-block ...`)**:
  Sway starts the session target with `--no-block` so the desktop becomes
  interactive immediately without waiting for network-dependent or slower user
  units to finish initializing.
- **Split unlocked vs. locked idle timers (`swayidle-unlocked.service` and
  `swayidle-locked.service`)**: Separating normal idle timeouts from
  locked-screen DPMS timeouts allows `$mod+Shift+i` (idle inhibit) to pause
  normal screen blanking during video playback or long builds while still
  letting a manually locked screen power off its display quickly.
- **Cached night-light coordinates (`wlsunset.service`, `redshift.service`, and
  `wlsunset-env.service`)**: `wlsunset` and `redshift` read cached latitude and
  longitude from `~/.config/wlsunset.env` so they can start immediately offline.
  Each daemon pulls in the oneshot `wlsunset-env.service` through `Wants=`, and
  that unit runs [`wlsunset-location`](tools.md#wlsunset-location) before the
  daemon starts.

## Unit overview

| Unit                              | Machine    | Purpose                                                                 |
| :-------------------------------- | :--------- | :---------------------------------------------------------------------- |
| `awww-daemon.service`             | `thinkpad` | Wallpaper daemon used by [`sw`](../desktop/wallpapers.md)               |
| `cliphist.service`                | `thinkpad` | Watches the Wayland clipboard (`wl-paste --watch cliphist store`)       |
| `polkit-agent.service`            | Both       | Authentication agent (`wrapper_polkit.sh`)                              |
| `swayidle-unlocked.service`       | `thinkpad` | Normal session idle and lock timeouts                                   |
| `swayidle-locked.service`         | `thinkpad` | Short DPMS display-off timeout while locked                             |
| `wlsunset.service`                | `thinkpad` | Color-temperature adjustment using cached coordinates                   |
| `redshift.service`                | `optiplex` | Color-temperature adjustment using cached coordinates                   |
| `wlsunset-env.service`            | Both       | Generates `~/.config/wlsunset.env` for `wlsunset` and `redshift`        |
| `calibre-sync.service` / `.timer` | `thinkpad` | Syncs `~/Library` to Google Drive (see [Calibre sync](calibre-sync.md)) |

## Inspecting units

```bash
systemctl --user status UNIT
journalctl --user -u UNIT -e
```
