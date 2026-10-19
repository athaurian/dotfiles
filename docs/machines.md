# Machines

This repository runs on two machines, `thinkpad` and `optiplex`, and those are
their actual hostnames. The hostname decides which set of programs each machine
gets. The `optiplex` hostname selects the i3 setup. Every other hostname gets
the `thinkpad` setup, laptop or not.

`thinkpad` is a ThinkPad L14 Gen 1 laptop, and it is the machine I use daily. It
runs Sway on Wayland.

`optiplex` is an OptiPlex 5060 desktop that I only use sometimes. Its GPU is
[an ancient NVIDIA card from the Egyptian era](https://www.techpowerup.com/gpu-specs/geforce-gt-630-rev-2.c2376),
and it does not run Wayland without issues, so the machine runs i3 on X11
instead.

Almost every desktop component exists twice, once per machine. `dunst` is the
exception, which runs just fine on both machines from one shared configuration
file.

| Component            | thinkpad (Sway)          | optiplex (i3)            |
| -------------------- | ------------------------ | ------------------------ |
| Window manager       | Sway                     | i3                       |
| Window compositing   | Built into Sway          | picom (an extra process) |
| Status bar           | Waybar                   | Polybar                  |
| Application launcher | fuzzel                   | rofi                     |
| Terminal             | foot                     | kitty                    |
| Screen locker        | swaylock                 | i3lock                   |
| Idle handling        | swayidle user units      | xset timer plus xss-lock |
| Color temperature    | wlsunset                 | redshift                 |
| Wallpaper            | sw with the awww backend | sw with the feh backend  |
| Screenshots          | grim with satty          | flameshot                |
| Notifications        | dunst                    | dunst                    |
| Session startup      | sway-session.target      | i3-session.target        |

Machine selection happens in
[`home/.chezmoiignore`](https://github.com/athaurian/dotfiles/blob/main/home/.chezmoiignore)
and
[`data/packages.json`](https://github.com/athaurian/dotfiles/blob/main/data/packages.json).
