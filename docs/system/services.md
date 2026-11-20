# Services

Background daemons are managed as [user units](../glossary.md#systemd-user-unit)
rather than as bare `exec` lines in the window manager configuration. The two
approaches differ in what they provide.

| Property        | User unit                       | Bare `exec` line             |
| :-------------- | :------------------------------ | :--------------------------- |
| Restart policy  | Declared per unit               | None                         |
| Log stream      | Per unit, via the user journal  | None per daemon              |
| Source location | `home/dot_config/systemd/user/` | Window manager configuration |

## Design choices

Three mechanisms address distinct startup and session problems. The table names
each mechanism, and the following subsections state the constraint it resolves.

| Choice                          | Units involved                                                 | Mechanism                                                                                                                |
| :------------------------------ | :------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| Non-blocking compositor startup | `sway-session.target`, `i3-session.target`                     | The [compositor](../glossary.md#compositor) starts the [session target](../glossary.md#session-target) with `--no-block` |
| Split idle timers               | `swayidle-unlocked.service`, `swayidle-locked.service`         | Separate timeouts for unlocked and locked sessions                                                                       |
| Generated night-light data      | `wlsunset.service`, `redshift.service`, `wlsunset-env.service` | A oneshot unit writes coordinates before the daemons start                                                               |

### Non-blocking compositor startup

By default, starting a unit returns only after the target and the units it pulls
in have finished starting. Because both compositors issue the start command
during their own initialization, a slow or network-dependent user unit would
delay the first interactive frame. They therefore start their session targets
without blocking. The job is queued and the command returns immediately,
decoupling startup latency from the readiness of optional services.

### Split idle timers

Normal blanking and locked-screen blanking serve different purposes. They use
separate units.

| Unit                        | Timeout                                                |
| :-------------------------- | :----------------------------------------------------- |
| `swayidle-unlocked.service` | Normal screen-blanking timeout                         |
| `swayidle-locked.service`   | Short [DPMS](../glossary.md#dpms) timeout while locked |

Normal blanking should not interrupt work, but a locked screen should power off
quickly. Because the units are separate, the lock script can stop one and start
the other without changing the normal idle policy. Toggling the idle inhibitor
pauses normal blanking during video playback or long builds, while the
locked-screen timeout stays in effect. For the X11 profile, the timeout values
are hand-maintained in `home/.chezmoidata.toml` and restored by the idle toggle
script.

### Generated night-light data

A daemon that needs coordinates should not perform the lookup itself, because
that would put a geolocation request on its startup path. Coordinates are
therefore produced by a separate [oneshot unit](../glossary.md#oneshot-unit),
and the daemons are ordered behind it and read its output through the
environment. Lookup logic lives in one place rather than in each daemon.

| Element     | Mechanism                                           |
| :---------- | :-------------------------------------------------- |
| Producer    | `wlsunset-env.service`, running `wlsunset-location` |
| Hand-off    | `~/.config/wlsunset.env`                            |
| Dependency  | `Wants=wlsunset-env.service` in each daemon         |
| Ordering    | `After=` that unit in each daemon                   |
| Consumption | `EnvironmentFile=` in each daemon                   |

Location sources and their order are given under
[`wlsunset-location`](tools.md#wlsunset-location). The oneshot performs the
lookup, which keeps the daemons themselves from making any network request.

## Unit overview

| Unit                              | Machine    | Purpose                                                                 |
| :-------------------------------- | :--------- | :---------------------------------------------------------------------- |
| `awww-daemon.service`             | `thinkpad` | Wallpaper daemon used by [`sw`](../desktop/wallpapers.md)               |
| `cliphist.service`                | `thinkpad` | Watches the Wayland clipboard (`wl-paste --watch cliphist store`)       |
| `polkit-agent.service`            | Both       | Authentication agent (`wrapper_polkit.sh`)                              |
| `syncthing.service`               | Both       | Enables the distro-provided Syncthing user unit                         |
| `swayidle-unlocked.service`       | `thinkpad` | Normal session idle and lock timeouts                                   |
| `swayidle-locked.service`         | `thinkpad` | Short DPMS display-off timeout while locked                             |
| `wlsunset.service`                | `thinkpad` | Color-temperature adjustment using generated data                       |
| `redshift.service`                | `optiplex` | Color-temperature adjustment using generated data                       |
| `wlsunset-env.service`            | Both       | Generates `~/.config/wlsunset.env` for `wlsunset` and `redshift`        |
| `calibre-sync.service` / `.timer` | `thinkpad` | Syncs `~/Library` to Google Drive (see [Calibre sync](calibre-sync.md)) |
| `calibre-sync-netmon.service`     | `thinkpad` | Starts a sync shortly after NetworkManager reconnects                   |

## Inspecting units

The status, log, and restart commands are shared with the failure workflow in
[Inactive user service](../troubleshooting.md#inactive-user-service).
