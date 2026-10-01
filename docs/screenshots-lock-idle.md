# Screenshots, lock, and idle

The following shortcuts control screenshots, the screen locker, and the idle
timer:

- Screenshots go to the clipboard. `Print` captures the full screen,
  `Shift+Print` captures a region, and `Control+Print` captures the focused
  window on both machines. thinkpad captures with `grim` and annotates with
  `satty`, while optiplex uses `flameshot`.
- `$mod+Shift+x` locks the screen with the `lock.sh` script in
  `home/dot_config/sway/scripts/` on thinkpad and `home/dot_config/i3/scripts/`
  on optiplex. The script uses `swaylock` on thinkpad and `i3lock` on optiplex.
- `$mod+Shift+i` toggles the idle timer. thinkpad runs the timer with its
  `swayidle` user units. optiplex sets the timer with `xset s 20 10` and locks
  through `xss-lock`, and it never suspends on idle.
