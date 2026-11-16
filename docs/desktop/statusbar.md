# Status bar

`thinkpad` runs Waybar on Wayland; `optiplex` runs Polybar on X11.

<figure class="screenshot">
  <img src="../images/bar-light.webp#only-light" alt="The Waybar status bar in light mode.">
  <img src="../images/bar.webp#only-dark" alt="The Waybar status bar in dark mode.">
</figure>

## Module behavior and workarounds

- **Media playback (`mpris` / `playerctl`)**: Combines `playerctl --follow` with
  a 1-second fallback poll. Relying on `--follow` alone leaves stale track
  titles on the bar when a browser tab or media player closes abruptly without
  emitting a final D-Bus `Stopped` signal.
- **Package updates (`checkupdates` + `paru -Qum`)**: Queries official Arch
  repos and the AUR on a slow interval after startup, switching to a shorter
  retry interval whenever the check runs before network connectivity is up.
- **Do Not Disturb (`dunst-dnd.sh`)**: Toggles `dunst` between pause level `0`
  (all notifications shown) and pause level `50` (normal notifications silenced,
  while critical rules configured at pause level `90` in
  [Applications](applications.md#notifications-and-do-not-disturb-dunst) still
  break through).
- **CJK glyph rendering (Polybar)**: Polybar adds **Noto Sans CJK JP** as
  `font-4` so Japanese and Chinese media titles and window titles render without
  missing glyphs. Waybar's font chain contains only `Geist Mono` and
  `GeistMono Nerd Font Mono`.

## Patched Polybar on `optiplex`

`optiplex` installs `polybar-pinned` from the
[`forge`](https://github.com/athaurian/forge) repository instead of the standard
`polybar` package. The package applies a layout patch to Polybar's renderer.

Upstream Polybar starts the right module block after the center block. On
`optiplex`'s `1366×768` display, a long centered window title therefore pushes
the clock, DND indicator, and system tray past the right edge. The patch places
the right block at `bar_width - right_width` instead, keeping those modules
visible.
