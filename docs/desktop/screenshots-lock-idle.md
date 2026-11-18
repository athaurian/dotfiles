# Screenshots, lock, and idle

Every screenshot is saved to `~/Pictures/Screenshots/` with a timestamped
filename and copied to the clipboard at the same time.

## Shortcuts

| Shortcut        | Action                  | `thinkpad` (Wayland)                                            | `optiplex` (X11)                                     |
| :-------------- | :---------------------- | :-------------------------------------------------------------- | :--------------------------------------------------- |
| `Print`         | Full screen             | `grim` (+ optional `satty` editor) + `wl-copy`                  | `flameshot full -c`                                  |
| `Shift+Print`   | Rectangular region      | `slurp` + `grim`                                                | `flameshot gui -c`                                   |
| `Control+Print` | Single window           | Focused window's dimensions from `swaymsg -t get_tree` + `grim` | `xdotool getactivewindow` + `flameshot gui --region` |
| `$mod+Shift+x`  | Lock screen immediately | `swaylock`                                                      | `i3lock`                                             |
| `$mod+Shift+i`  | Toggle idle inhibitor   | Pauses/resumes `swayidle` timeouts                              | Toggles X11 screensaver and DPMS timeouts            |

### Why `Control+Print` behaves differently on each machine

On `thinkpad`, `Control+Print` queries Sway's window tree for the focused
window's dimensions and captures that rectangle with `grim`. No click prompt
appears.

On `optiplex`, the script reads the active X11 window ID with
`xdotool getactivewindow`, derives its geometry, and opens Flameshot on that
region.

## Lock screen

<figure class="screenshot">
  <img src="../images/lock-light.webp#only-light" alt="The lock screen with a blurred wallpaper behind the clock.">
  <img src="../images/lock.webp#only-dark" alt="The lock screen with a blurred wallpaper behind the clock.">
</figure>

While the screen is locked on `thinkpad`, a dedicated `swayidle-locked.service`
shortens the display-off timeout so waking the screen to check a notification
turns the backlight back off quickly if you do not unlock.

## Regenerating documentation screenshots

From `~/.local/share/chezmoi`, run `make shots` to cycle through dark and light
modes and capture fresh desktop, picker, and editor images into `docs/images/`.
The lock-screen and Discord captures need manual work; see `meta/shots.md`.
