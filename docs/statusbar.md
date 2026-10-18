# Status bar

`thinkpad` starts Waybar from the Sway config, with its files under
[`home/dot_config/waybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/waybar/).
`optiplex` starts Polybar as `polybar main` from the i3 session's
`autostart.sh`, and `$mod+Shift+c` restarts it. Its files live under
[`home/dot_config/polybar/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/polybar/).
Each bar keeps its module scripts in a `scripts/` directory of its own.
