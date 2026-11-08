# Background services

Units live in
[`home/dot_config/systemd/user/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/systemd/user/).
The `sway-session.target` and `i3-session.target` units start with the session
on `thinkpad` and `optiplex`, respectively.

If a unit fails:

- Run `systemctl --user status UNIT` to show its state.
- Run `journalctl --user -u UNIT` to see the logs.

Replace `UNIT` with the name of the unit.
