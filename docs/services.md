# Background services

Units live in `home/dot_config/systemd/user/`. The `sway-session.target` and
`i3-session.target` units each have a `.wants/` directory listing the units that
start with the session. thinkpad uses `sway-session.target.wants`, and optiplex
uses `i3-session.target.wants`. Manage them with `systemctl --user` and
`journalctl --user -u UNIT`. Replace `UNIT` with the unit name.
