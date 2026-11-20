# Machines

The `chezmoi` source tree targets two machines. Hostname is the selection
mechanism: any hostname other than `optiplex` resolves to the `thinkpad`
profile.

- **`thinkpad` (ThinkPad L14 Gen 1):** Runs Sway on
  [Wayland](glossary.md#wayland). This is the default profile.
- **`optiplex` (Dell OptiPlex 5060):** Carries an NVIDIA GeForce GT 630 (rev. 2)
  on the legacy proprietary driver branch. Because Wayland sessions were
  unreliable on that combination in my testing, I run i3 on
  [X11](glossary.md#x11) on this machine.

## Differences between `thinkpad` and `optiplex`

The two profiles share an application layer and diverge at the display-server
layer. Keeping the shared layer constant reduces machine-specific branching in
the templates.

### Shared applications

Both machines use the same applications for these roles:

| Role                | Application      |
| :------------------ | :--------------- |
| Terminal            | `kitty`          |
| Multiplexer         | `zellij`         |
| Shell               | `bash`           |
| Editor              | `nvim`           |
| Notification daemon | `dunst`          |
| File manager        | `thunar`         |
| Browser             | `helium-browser` |
| Document viewer     | `zathura`        |

### Display-server differences

The display-server layer changes the tools chosen for these roles:

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

Focused-window capture is the most consequential behavioral difference between
the profiles. See
[Screenshots, lock, and idle](desktop/screenshots-lock-idle.md#focused-window-capture-differences).
