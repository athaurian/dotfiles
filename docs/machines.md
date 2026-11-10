# Machines

My setup runs on two machines, named after their hostnames: `thinkpad` and
`optiplex`. The hostname selects each machine's programs. `optiplex` gets the i3
setup, while any other hostname gets the `thinkpad` setup, laptop or not.

`thinkpad` is a ThinkPad L14 Gen 1 laptop, and it's the machine I use daily. It
runs Sway on Wayland.

`optiplex` is an OptiPlex 5060 desktop that I only use sometimes. Its GPU is an
[NVIDIA GeForce GT 630 (rev. 2)](https://www.techpowerup.com/gpu-specs/geforce-gt-630-rev-2.c2376).
Wayland doesn't work reliably with this GPU, so I run i3 on X11 instead.

| Component            | thinkpad (Sway)            | optiplex (i3)            |
| -------------------- | -------------------------- | ------------------------ |
| Window management    | Sway (Wayland compositor)  | i3 (X11 window manager)  |
| Compositor           | Built into Sway            | picom (separate process) |
| Status bar           | Waybar                     | Polybar                  |
| Application launcher | fuzzel                     | rofi                     |
| Terminal             | kitty                      | kitty                    |
| Screen locker        | swaylock                   | i3lock                   |
| Idle handling        | swayidle user units        | xset timer plus xss-lock |
| Color temperature    | wlsunset                   | redshift                 |
| Wallpaper            | sw with the awww backend   | sw with the feh backend  |
| Screenshots          | grim with satty            | flameshot                |
| Notifications        | dunst                      | dunst                    |
| Clipboard history    | cliphist and the picker    | None                     |
| Tray applets         | Started by the Sway config | Started by `applets.sh`  |
| Session startup      | sway-session.target        | i3-session.target        |

`cliphist` and the picker require Wayland, and `optiplex` has no brightness key
bindings.

`Control+Print` captures the focused window on both machines, but by different
methods. `thinkpad` computes the window rectangle itself, captures it with
`grim`, and copies it to the clipboard before `satty` opens. `optiplex` computes
the same rectangle with `xdotool` and opens `flameshot` with a crop region for
that window, so `flameshot` updates the clipboard only after you confirm the
crop.
