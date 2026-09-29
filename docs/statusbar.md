# Status bar

Each machine runs its own bar, and both follow the active palette without manual
edits: thinkpad runs Waybar, started by Sway's bar block and styled from
`style.css.tmpl`; optiplex runs Polybar, started as `polybar main` by the
session autostart script and restarted by `$mod+Shift+c`.

## What the bar shows

| Group  | thinkpad (Waybar)                                                 | optiplex (Polybar)                                       |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------- |
| Left   | Workspaces, resize indicator, music                               | Workspaces, resize indicator, music                      |
| Center | Focused window title                                              | Focused window title                                     |
| Right  | CPU, memory, updates, sound, battery, tray, clock, do not disturb | CPU, memory, updates, sound, tray, clock, do not disturb |

Long window titles shorten to fit the bar. The battery module is thinkpad's
hardware; optiplex is a desktop without one. The tray holds the network and
Bluetooth applet icons on both machines. The full module inventory, including
what each custom script does, is in [FEATURES.md](../FEATURES.md).

Click CPU to open btop in a centered floating window.

## Control music from the bar

The music module shows the current track whenever something plays — a browser, a
music app — and hides when nothing does. Click the track to play or pause,
scroll up for the next track, and scroll down for the previous one.

## Install updates from the bar

The bar counts pending repository and AUR updates and names the first few
packages in its tooltip. Click the count to open `topgrade` in a scratchpad
terminal; clicking again hides it, clicking once more brings it back, and
closing the window lets the next click start a fresh run. Which packages the
count covers is described in [Installation](installation.md).

## Silence notifications from the bar

Press `$mod+Shift+d` or click the do not disturb indicator to silence popups.
Direct feedback still appears — toggle and wallpaper messages — and locking the
screen hides even those. Press the shortcut or click again to let notifications
through.
