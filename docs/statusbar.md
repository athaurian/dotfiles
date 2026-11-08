# Status bar

`thinkpad` runs Waybar, and `optiplex` runs Polybar.

<figure class="screenshot">
  <img src="images/bar-light.webp#only-light" alt="The Waybar status bar in light mode.">
  <img src="images/bar.webp#only-dark" alt="The Waybar status bar in dark mode.">
</figure>

Press `$mod+Shift+c` to restart the bar on both machines. Waybar's files live
under
[`home/dot_config/waybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/waybar/),
Polybar's under
[`home/dot_config/polybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/polybar/).

Both bars check for updates once an hour and re-check when a topgrade run
finishes. Only Waybar lists the pending packages in a tooltip. Polybar has no
tooltip support, so its module shows only the count.

Polybar needs a CJK font family for non-Latin text. Without one, non-Latin text
in module output (song titles, window titles) is silently dropped.
