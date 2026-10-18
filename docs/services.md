# Background services

Units live in
[`home/dot_config/systemd/user/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/systemd/user/).
The `sway-session.target` and `i3-session.target` units each have a `.wants/`
directory listing the units that start with the session. `thinkpad` uses
`sway-session.target.wants`, and `optiplex` uses `i3-session.target.wants`. When
a unit acts up, `systemctl --user` shows its state and
`journalctl --user -u UNIT` has the logs. Swap the unit's name in for `UNIT`.
