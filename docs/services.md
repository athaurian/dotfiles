# Background services

This page explains the programs that run without a window. It covers the session
group, power controls, and three maintenance services. It assumes you are
comfortable running commands in a terminal and nothing else. A _systemd user
service_ is a background program that systemd starts for your login rather than
for the whole machine.

## Work with the session group

Logging in starts the desktop services together. Logging out stops them
together. The group holds the notification daemon, the clipboard keeper, the
policy agent, the idle rules, the night light, and the applet services.

Press `Super+Shift+E` to log out. If a service misbehaves, check it with
`journalctl --user -u SERVICE_NAME`, replacing `SERVICE_NAME` with the service
name.

## Control the session

You can control the Sway session with the four shortcuts in the following table.
Each one opens a confirmation menu with **yes** and **no**. Type or press `Up`
and `Down`, then press `Enter` to confirm and `Escape` to cancel. Pressing the
same shortcut again dismisses the menu.

| Shortcut                | Action    |
| :---------------------- | :-------- |
| `Super+Shift+Backspace` | Power off |
| `Super+Shift+r`         | Reboot    |
| `Super+Shift+z`         | Suspend   |
| `Super+Shift+e`         | Logout    |

Power off, reboot, and logout save your Sway session first. Suspend does not
save, because the session keeps running while the machine sleeps. For more
information about what gets saved, see [Session manager](session-manager.md).

## Watch for config drift

Your installed files are checked once per day, and the check stays silent when
everything matches. When files differ, it sends one notice with the count and a
short preview, plus a hint to run `chezmoi diff`. It also flags stray files left
in managed script folders.

## Mirror the ebook library

Your books sync to Google Drive every 30 minutes. Every EPUB and PDF in the
`~/Library` directory is staged under a flat name built from calibre metadata in
`Author - Series NN - Title` form, then mirrored to `gdrive:Books`.

When offline, the sync stages locally and skips the upload with a clean exit
instead of failing. A reconnect watcher starts a sync promptly once the network
is back, so you do not wait for the next 30-minute tick.

The sync needs an `rclone` remote named `gdrive` signed in to Google Drive,
which this repository does not set up. Without books, or without that remote,
the sync fails and the journal says why. If you do not keep an ebook library,
remove the `symlink_calibre-sync.timer.tmpl` file from the
`sway-session.target.wants/` directory before applying. Check on it with
`journalctl --user -u calibre-sync`.

## Shift screen color at night

The night light warms the screen after sunset based on your location. Run the
`wlsunset-location` helper once per machine to record it. Your location stays in
a private machine-local file outside version control, so it never syncs with the
repo.
