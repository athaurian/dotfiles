# Status bar

`thinkpad` starts Waybar from the Sway config, and `optiplex` starts Polybar as
`polybar main` from the i3 session's `autostart.sh` script.

<figure class="screenshot">
  <img src="images/bar-light.webp#only-light" alt="The Waybar status bar in light mode.">
  <img src="images/bar.webp#only-dark" alt="The Waybar status bar in dark mode.">
</figure>

Press `$mod+Shift+c` to restart the bar on both machines. Waybar's files live
under
[`home/dot_config/waybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/waybar/),
Polybar's under
[`home/dot_config/polybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/polybar/).
Each bar keeps its module scripts in a `scripts/` directory of its own.
