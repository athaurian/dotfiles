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

Both bars check for updates once an hour and re-check when a topgrade run
finishes. Only Waybar lists the pending packages in a tooltip; Polybar has no
tooltip support, so its module shows the count alone.

Polybar only falls back to the families listed in its `font-N` entries, so
`font-4` in `config.ini` points at the CJK family from
[`home/.chezmoidata.toml`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoidata.toml).
Without it, non-Latin text in module output (song titles, window titles) is
silently dropped rather than rendered.
