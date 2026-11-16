# Machines

The repository's `chezmoi` source tree targets two machines. Any hostname other
than `optiplex` resolves to the `thinkpad` profile.

- **`thinkpad` (ThinkPad L14 Gen 1)**: Runs Sway on Wayland.
- **`optiplex` (Dell OptiPlex 5060)**: Has an old NVIDIA GeForce GT 630 (rev. 2)
  tethered to the legacy proprietary driver branch, where Wayland compositors
  are unreliable. It runs i3 on X11 with `picom` so the workflow and keybindings
  match `thinkpad` without fighting the GPU driver.

## Differences between `thinkpad` and `optiplex`

Both machines share the same terminal (`kitty`), multiplexer (`zellij`), shell
(`bash`), editor (`nvim`), notification daemon (`dunst`), file manager
(`thunar`), browser (`helium-browser`), and document viewer (`zathura`). Only
the display-server layer swaps between Wayland and X11:

| Role                 | `thinkpad` (Wayland)                         | `optiplex` (X11)                                |
| :------------------- | :------------------------------------------- | :---------------------------------------------- |
| Window manager       | Sway                                         | i3 + `picom`                                    |
| Status bar           | Waybar                                       | Polybar (`polybar-pinned` for 1366px displays)  |
| App launcher & menus | `fuzzel`                                     | `rofi`                                          |
| Wallpaper daemon     | `awww`                                       | `feh`                                           |
| Screen lock          | `swaylock`                                   | `i3lock`                                        |
| Idle manager         | `swayidle`                                   | `xss-lock` + X11 DPMS                           |
| Night light          | `wlsunset`                                   | `redshift`                                      |
| Screenshots          | `grim` + `slurp`                             | `flameshot`                                     |
| Clipboard history    | `cliphist` + `wl-paste` + `clipboard-picker` | Standard X11 selection only (no history picker) |

For the difference in how focused-window screenshots (`Control+Print`) behave
across Sway and i3, see
[Screenshots, lock, and idle](desktop/screenshots-lock-idle.md).
