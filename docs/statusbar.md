# Status bar

I run Waybar on `thinkpad` and Polybar on `optiplex`.

<figure class="screenshot">
  <img src="images/bar-light.webp#only-light" alt="The Waybar status bar in light mode.">
  <img src="images/bar.webp#only-dark" alt="The Waybar status bar in dark mode.">
</figure>

Press `$mod+Shift+c` to restart the bar on both machines. I keep Waybar's files
under
[`home/dot_config/waybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/waybar/),
and Polybar's under
[`home/dot_config/polybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/polybar/).

Polybar requires a CJK font family for non-Latin text. Without one, non-Latin
text in module output (song titles, window titles) is silently dropped.

On `optiplex`, Polybar is installed from `polybar-pinned` in `forge`. That build
pins the modules on the right side of the bar to the bar edge, so a long window
title is drawn underneath the clock and systray instead of pushing them past the
1366px bar. The window-title and MPRIS caps are sized from the remaining columns
instead of being chosen by eye.
