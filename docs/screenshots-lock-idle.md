# Screenshots, lock, and idle

The following shortcuts control screenshots, the screen locker, and the idle
timer. Every binding is the same on both machines, and only the programs and
mechanisms differ.

| Shortcut        | Action                      | thinkpad                                              | optiplex                                               |
| --------------- | --------------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| `Print`         | Full screen to clipboard    | `grim`                                                | `flameshot`                                            |
| `Shift+Print`   | Region to clipboard         | `grim`, annotate with `satty`                         | `flameshot`                                            |
| `Control+Print` | Focused window to clipboard | `grim`                                                | `flameshot`                                            |
| `$mod+Shift+x`  | Lock the screen             | `swaylock` via `home/dot_config/sway/scripts/lock.sh` | `i3lock` via `home/dot_config/i3/scripts/lock.sh`      |
| `$mod+Shift+i`  | Toggle the idle timer       | `swayidle` user units                                 | `xset s 20 10` with `xss-lock`, never suspends on idle |
