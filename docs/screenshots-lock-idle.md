# Screenshots, lock, and idle

- Screenshots go to the clipboard. `Print` captures the full screen,
  `Shift+Print` captures a region, and `Control+Print` captures the focused
  window on both machines. thinkpad captures with `grim` and annotates with
  `satty`, while optiplex uses `flameshot`.
- `$mod+Shift+x` locks the screen by running `lock.sh` from the machine's config
  directory. The script uses `swaylock` on thinkpad and `i3lock` on optiplex.
- `$mod+Shift+i` toggles the idle timer. thinkpad runs the timer with its
  `swayidle` user units. optiplex sets the timer with `xset s 20 10` and locks
  through `xss-lock`, and it never suspends on idle.
