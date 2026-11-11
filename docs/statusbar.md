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

Polybar needs a CJK font family for non-Latin text. Without one, non-Latin text
in module output (song titles, window titles) is silently dropped.
