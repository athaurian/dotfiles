# Keybindings

`$mod` is bound to the `Super` (Windows) key. Almost all bindings are identical
across Sway (`thinkpad`) and i3 (`optiplex`). The few laptop- or Wayland-only
shortcuts are marked in the tables.

## Window management and focus

| Binding                                                                    | Action                                             |
| :------------------------------------------------------------------------- | :------------------------------------------------- |
| `$mod+h` / `$mod+j` / `$mod+k` / `$mod+l` (or arrow keys)                  | Move focus left / down / up / right                |
| `$mod+Shift+h` / `$mod+Shift+j` / `$mod+Shift+k` / `$mod+Shift+l` (arrows) | Move the focused window left / down / up / right   |
| `$mod+a` / `$mod+Shift+a`                                                  | Focus the parent / child container                 |
| `$mod+1` … `$mod+0`                                                        | Switch to workspace `1`–`10`                       |
| `$mod+Shift+1` … `$mod+Shift+0`                                            | Move the focused window to workspace `1`–`10`      |
| `$mod+c`                                                                   | Center the focused floating window                 |
| `$mod+q`                                                                   | Close the focused window                           |
| `$mod+f`                                                                   | Toggle fullscreen                                  |
| `$mod+Shift+Space`                                                         | Toggle floating / tiled for the focused window     |
| `$mod+Space`                                                               | Switch focus between the tiled and floating layers |

## Layout and scratchpads

| Binding                        | Action                                                                   |
| :----------------------------- | :----------------------------------------------------------------------- |
| `$mod+o` / `$mod+v`            | Split horizontally / vertically                                          |
| `$mod+s` / `$mod+w` / `$mod+p` | Stacking / tabbed / toggle split layout                                  |
| `$mod+r`                       | Enter resize mode (`h/j/k/l` or arrows to resize, `Enter`/`Esc` to exit) |
| `$mod+Return`                  | Open a terminal                                                          |
| `$mod+grave`                   | Toggle the dropdown terminal scratchpad                                  |
| `$mod+Shift+minus`             | Send the focused window to the general scratchpad                        |
| `$mod+minus`                   | Cycle through general scratchpad windows                                 |

## Applications and pickers

| Binding                         | Action                                                                        |
| :------------------------------ | :---------------------------------------------------------------------------- |
| `$mod+d`                        | Toggle the application launcher (`fuzzel` / `rofi`)                           |
| `$mod+b` / `$mod+e`             | Open the browser / file manager                                               |
| `$mod+Ctrl+v`                   | Open [`clipboard-picker`](pickers.md#clipboard-history) (**`thinkpad` only**) |
| `$mod+u`                        | Toggle Topgrade                                                               |
| `$mod+Shift+p` / `$mod+Shift+b` | Open the password manager / Bluetooth manager                                 |
| `$mod+Shift+v`                  | Open `pavucontrol`                                                            |
| `$mod+Shift+t`                  | Toggle dark and light theme mode across the desktop                           |

## Screenshots, session, and notifications

| Binding                                                                   | Action                                                        |
| :------------------------------------------------------------------------ | :------------------------------------------------------------ |
| `Print` / `Shift+Print` / `Control+Print`                                 | Capture full screen / region / focused window                 |
| `$mod+Shift+x`                                                            | Lock the screen immediately                                   |
| `$mod+Shift+i`                                                            | Toggle the idle / sleep inhibitor                             |
| `$mod+Shift+d`                                                            | Toggle Do Not Disturb                                         |
| `$mod+n` / `$mod+Shift+n`                                                 | Close the latest / all `dunst` notifications                  |
| `$mod+Shift+c`                                                            | Reload the window manager (and restart Polybar on `optiplex`) |
| `$mod+Shift+BackSpace` / `$mod+Shift+r` / `$mod+Shift+z` / `$mod+Shift+e` | Power off / reboot / suspend / log out                        |

## Media and hardware keys

| Binding                                | Action                                             |
| :------------------------------------- | :------------------------------------------------- |
| `XF86AudioRaiseVolume` / `LowerVolume` | Raise / lower the default sink volume with `pactl` |
| `XF86AudioMute` / `AudioMicMute`       | Toggle speaker mute / microphone mute              |
| `XF86AudioPlay` / `Next` / `Prev`      | Control the active MPRIS player with `playerctl`   |
| `XF86MonBrightnessUp` / `Down`         | Adjust backlight brightness (**`thinkpad` only**)  |
