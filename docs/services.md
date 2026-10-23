# Background services

Units live in
[`home/dot_config/systemd/user/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/systemd/user/).
The `sway-session.target` and `i3-session.target` units each have a `.wants/`
directory listing the units that start with the session.

- `thinkpad` uses `sway-session.target.wants`.
- `optiplex` uses `i3-session.target.wants`.

When a unit acts up:

- Run `systemctl --user status UNIT` to show its state.
- Run `journalctl --user -u UNIT` to see the logs.

(Replace `UNIT` with the unit's name.)
