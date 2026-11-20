# Status bar

`thinkpad` runs Waybar on Wayland; `optiplex` runs Polybar on X11. The two bars
expose the same information through different module implementations.

<figure class="screenshot">
  <img src="../images/bar-light.webp#only-light" alt="The Waybar status bar in light mode.">
  <img src="../images/bar.webp#only-dark" alt="The Waybar status bar in dark mode.">
</figure>

## Module behavior and workarounds

The table records the component, polling interval, and fallback for each bar
concern.

| Concern         | Component                   | Interval | Fallback or retry                     |
| :-------------- | :-------------------------- | :------- | :------------------------------------ |
| Media playback  | `playerctl --follow`        | 1 s      | Poll corrects a missing Stopped event |
| Package updates | `checkupdates`, `paru -Qum` | 3600 s   | 300 s on failure; 30–60 s offline     |
| Do Not Disturb  | `dunst-dnd.sh`              | 5 s      | Signal-driven refresh                 |
| CJK glyphs      | `font-4` (Polybar)          | —        | Explicit Noto Sans CJK JP entry       |

| Pause level | Effect                            |
| :---------- | :-------------------------------- |
| `0`         | All notifications are shown       |
| `50`        | Normal notifications are silenced |

Each row addresses a distinct rendering, timing, or notification concern:

- **Stale media titles**: Browsers and media players can close abruptly without
  emitting a final D-Bus `Stopped` signal. `--follow` alone then leaves the last
  track title on the bar. The poll corrects it.
- **Update checks before networking**: The first check can run before the
  network is available. The shorter retry interval recovers without waiting for
  the full interval.
- **Notification levels**: Rules configured at pause level `90` in
  [Applications](applications.md#notifications-and-do-not-disturb-dunst) are
  still displayed.

Font resolution differs between the bars.

| Bar     | Font resolution                                                     | Consequence                 |
| :------ | :------------------------------------------------------------------ | :-------------------------- |
| Polybar | Renders only fonts in its own list                                  | CJK needs an explicit entry |
| Waybar  | Delegates missing glyphs to Fontconfig via the `monospace` fallback | A two-font chain suffices   |

## Patched Polybar on `optiplex`

`optiplex` installs `polybar-pinned` from the
[`forge`](https://github.com/athaurian/forge) repository rather than the
standard `polybar` package. The pinned package applies a layout patch to
Polybar's renderer.

Upstream Polybar starts the right module block after the center block. On
`optiplex`'s `1366×768` display, a long centered window title therefore pushes
the clock, DND indicator, and system tray past the right edge. The patch places
the right block at `bar_width - right_width` instead, keeping those modules
visible.
