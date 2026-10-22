# Background services

Units live in
[`home/dot_config/systemd/user/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/systemd/user/).
The `sway-session.target` and `i3-session.target` units each have a `.wants/`
directory listing the units that start with the session.

- `thinkpad` uses `sway-session.target.wants`.
- `optiplex` uses `i3-session.target.wants`.

When a unit acts up, run `systemctl --user status UNIT` to show its state and
`journalctl --user -u UNIT` to see the logs. Swap the unit's name in for `UNIT`.

The `cliphist` daemon on `thinkpad` fills the clipboard history the picker
browses. It runs `wl-paste --watch cliphist store`, so a history entry appears
as soon as you copy something. A fresh `chezmoi apply` adds the unit to
`sway-session.target.wants`, which needs a new login or a `daemon-reload` before
systemd picks it up.
