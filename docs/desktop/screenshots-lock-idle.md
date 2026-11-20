# Screenshots, lock, and idle

Every screenshot is saved to `~/Pictures/Screenshots/` with a timestamped
filename and copied to the clipboard at the same time. Capture commands differ
between profiles because Wayland and X11 expose different window-information
interfaces.

## Shortcuts

| Shortcut        | Action                  | `thinkpad` (Wayland)                                            | `optiplex` (X11)                                                 |
| :-------------- | :---------------------- | :-------------------------------------------------------------- | :--------------------------------------------------------------- |
| `Print`         | Full screen             | `grim` (+ optional `satty` editor) + `wl-copy`                  | `flameshot full -c`                                              |
| `Shift+Print`   | Rectangular region      | `slurp` + `grim`                                                | `flameshot gui -c`                                               |
| `Control+Print` | Single window           | Focused window's dimensions from `swaymsg -t get_tree` + `grim` | `xdotool getactivewindow` + `flameshot gui -c --region`          |
| `$mod+Shift+x`  | Lock screen immediately | `swaylock`                                                      | `i3lock`                                                         |
| `$mod+Shift+i`  | Toggle idle inhibitor   | Pauses/resumes `swayidle` timeouts                              | Toggles X11 screensaver and [DPMS](../glossary.md#dpms) timeouts |

### Focused-window capture differences

Both profiles derive the focused window's rectangle from the window manager, but
they use different interfaces and capture tools.

| Machine    | Geometry source                                   | Capture tool                    | Interaction                                   |
| :--------- | :------------------------------------------------ | :------------------------------ | :-------------------------------------------- |
| `thinkpad` | Sway window tree via `swaymsg -t get_tree`        | `grim` on the focused rectangle | Captures directly; no region-selection prompt |
| `optiplex` | `xdotool getactivewindow` and `getwindowgeometry` | `flameshot gui -c --region`     | Opens Flameshot on the supplied rectangle     |

## Lock screen

<figure class="screenshot">
  <img src="../images/lock-light.webp#only-light" alt="The lock screen with a blurred wallpaper behind the clock.">
  <img src="../images/lock.webp#only-dark" alt="The lock screen with a blurred wallpaper behind the clock.">
</figure>

While the screen is locked on `thinkpad`, the locked idle unit shortens the
display-off timeout. Waking the screen to check a notification turns the
backlight back off quickly if you do not unlock. The unlock action swaps the
normal idle unit back in.

## Regenerating documentation screenshots

To regenerate the documentation screenshots, run the automatic captures and then
the manual ones. The capture script stages windows on workspace 3. That
workspace must be empty before it runs. From `~/.local/share/chezmoi`:

1. Run `make shots` to cycle through dark and light modes and capture the
   desktop, picker, and editor images into `docs/images/`.
2. Capture the lock-screen and Discord images manually. Their steps are in
   [`meta/shots.md`](https://github.com/athaurian/dotfiles/blob/main/meta/shots.md).
