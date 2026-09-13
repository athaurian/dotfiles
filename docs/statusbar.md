# Status bar

The bar follows the active theme without config changes. It has three groups, as
listed in the following table:

| Group  | Shows                                                              |
| :----- | :----------------------------------------------------------------- |
| Left   | Workspaces, resize indicator, and music                            |
| Center | Focused window title                                               |
| Right  | System stats, updates, sound, battery, tray, clock, do not disturb |

The resize indicator appears only while you resize windows. Long window titles
are shortened to fit the bar.

## Control music from the bar

The left side shows the current track whenever something plays, such as in a
browser or a music app, and hides the track when nothing does. Click the track
to play or pause, scroll up for the next track, and scroll down for the previous
track.

## Install updates from the bar

The bar counts pending repository and AUR updates, and names the first few
packages in its tooltip. Click the count to open `topgrade` in a scratchpad
terminal. Clicking again hides it, and clicking once more brings it back. When
the window closes, the next click starts a fresh one. For package sources, see
[Installation](installation.md).

## Silence notifications from the bar

Press `Super+Shift+d` or click the do not disturb indicator to silence popups.
Direct feedback still appears, such as toggle and wallpaper messages, and
locking the screen hides even those. Press the shortcut or click again to let
notifications through. For dismissing single messages and browsing history, see
[Pickers](pickers.md).
