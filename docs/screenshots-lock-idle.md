# Screenshots, lock, and idle

These are the shortcuts for screenshots, the screen locker, and the idle timer.
As you'd expect, the keys are the same on both machines. Only the programs
behind them differ.

| Shortcut        | Action                      | thinkpad                                                                                                                                                            | optiplex                                                                                                                                                                |
| --------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Print`         | Full screen to clipboard    | `grim`                                                                                                                                                              | `flameshot`                                                                                                                                                             |
| `Shift+Print`   | Region to clipboard         | `grim`, annotate with `satty`                                                                                                                                       | `flameshot`                                                                                                                                                             |
| `Control+Print` | Focused window to clipboard | `grim`                                                                                                                                                              | `flameshot`                                                                                                                                                             |
| `$mod+Shift+x`  | Lock the screen             | `swaylock` via [`home/dot_config/sway/scripts/executable_lock.sh`](https://github.com/athaurian/dotfiles/blob/main/home/dot_config/sway/scripts/executable_lock.sh) | `i3lock` via [`home/dot_config/i3/scripts/executable_lock.sh.tmpl`](https://github.com/athaurian/dotfiles/blob/main/home/dot_config/i3/scripts/executable_lock.sh.tmpl) |
| `$mod+Shift+i`  | Toggle the idle timer       | `swayidle` user units                                                                                                                                               | `xset s 20 10` with `xss-lock`, never suspends on idle                                                                                                                  |

## Lock screen

<figure class="screenshot">
  <img src="images/lock-light.webp#only-light" alt="The lock screen with a blurred wallpaper behind the clock.">
  <img src="images/lock.webp#only-dark" alt="The lock screen with a blurred wallpaper behind the clock.">
</figure>
