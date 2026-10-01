# Machines

This repository runs on two machines, `thinkpad` and `optiplex`, and each
machine gets a different set of programs. The following table compares the
components on both machines and states how each pair relates.

| Component            | thinkpad (Sway)          | optiplex (i3)            | Relationship                                                                                                    |
| -------------------- | ------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Window manager       | Sway                     | i3                       | Same role, different programs                                                                                   |
| Window compositing   | Built into Sway          | picom                    | No direct counterpart. Wayland compositing is part of Sway itself, and optiplex needs picom as an extra process |
| Status bar           | Waybar                   | Polybar                  | Same role, different programs                                                                                   |
| Application launcher | fuzzel                   | rofi                     | Same role, different programs. Both also serve the confirmation menus                                           |
| Terminal             | foot                     | kitty                    | Same role, different programs                                                                                   |
| Screen locker        | swaylock                 | i3lock                   | Same role, different programs                                                                                   |
| Idle handling        | swayidle user units      | xset timer plus xss-lock | Similar purpose, different mechanisms. optiplex never suspends on idle                                          |
| Color temperature    | wlsunset                 | redshift                 | Same role, different programs, one session unit each                                                            |
| Wallpaper            | sw with the awww backend | sw with the feh backend  | Same script, different backend for each session type                                                            |
| Screenshots          | grim with satty          | flameshot                | Same bindings, different programs                                                                               |
| Notifications        | dunst                    | dunst                    | Same program on both machines, one shared configuration file                                                    |
| Session startup      | sway-session.target      | i3-session.target        | Parallel units that select what starts with the session                                                         |

The authoritative machine selection lives in `home/.chezmoiignore` and
`data/packages.json`.
