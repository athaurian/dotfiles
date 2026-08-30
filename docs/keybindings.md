# Keybindings

This page describes the keyboard shortcuts in this setup and how they are wired up. It covers what each shortcut does, why some depend on environment variables and wrapper scripts, and where to look for the definitive reference. It is written for people who are new to this kind of setup, so every term is defined the first time it appears.

## Background

SwayFX is a Wayland compositor, which is the program that draws your windows on the screen and positions them. A keybinding is a shortcut, a combination of keys that triggers an action. The config is written for SwayFX, and most shortcuts use the `Super` key, which is the Windows key on most keyboards.

This page has two parts. The first part covers how the shortcuts are wired up, because some of them call scripts and read environment variables rather than launching programs directly. The second part lists the shortcuts in a reference table, with the movement and layout controls explained in the following section.

## How application shortcuts are wired

### Environment variables

An environment variable is a named value that your shell and the programs you launch can read. The SwayFX config uses two of them for the file manager and password manager, named `FILEMANAGER` and `PASSWORD_MANAGER`.

If left unset, they default to `thunar` and `keepassxc` respectively. So pressing the file manager shortcut opens whatever `FILEMANAGER` points at, or `thunar` if you did not set it.

### Wrapper scripts

The browser shortcut works slightly differently. Instead of relying solely on an environment variable, it calls a wrapper script (`wrapper_browser.sh`). A wrapper script is a small program that determines which real program to run. This script respects `$BROWSER` if it is set, but if not, it falls back to the first available binary, trying `helium-browser`, then `firefox`, then `chromium`, and finally `google-chrome`.

### Default applications

When you open a link or a file from outside the file manager, for example clicking a link in a terminal or a chat app, your system must determine which program handles it. MIME types drive that choice. A MIME type is a label that describes what kind of content a file holds, like PDF or HTML. The mapping from MIME types to programs lives in `mimeapps.list`:

```ini
[Default Applications]
application/pdf=org.pwmt.zathura.desktop
text/html=helium.desktop;firefox.desktop;
x-scheme-handler/terminal=foot.desktop;
x-scheme-handler/http=helium.desktop;firefox.desktop;
x-scheme-handler/https=helium.desktop;firefox.desktop;
x-scheme-handler/about=helium.desktop;firefox.desktop;
x-scheme-handler/unknown=helium.desktop;firefox.desktop;
x-scheme-handler/discord=vesktop.desktop;
```

Each line names a MIME type on the left and the programs that may handle it on the right, separated by semicolon characters. The first program on each line is the preferred one, and the others are fallbacks. The `x-scheme-handler/*` lines cover URL schemes. Through these lines, your system opens `http://` links in the browser and `discord://` links in Vesktop. In this file the preferred browser is Helium, the browser this setup installs, with Firefox as the fallback.

### Other environment variables

Other environment variables live outside the SwayFX config. `EDITOR` lives in `~/.bash_profile`, and the `WLSUNSET_*` family lives in `~/.config/wlsunset.env`, a machine-local file that `wlsunset-location` generates; `~/.bash_profile` loads it and the wlsunset service reads it. The SwayFX autostart script (`autostart.sh`) bridges SwayFX and systemd, but it only imports a handful of session variables, such as `WAYLAND_DISPLAY` and `SWAYSOCK`, into the systemd user environment so GUI app services function properly.

Here is why that bridge exists. SwayFX sets some variables in its own session, but the background services that systemd starts do not see them by default. `autostart.sh` copies over the ones those services need, so a GUI app launched by systemd still receives the display information it needs.

## The shortcuts

The following table lists the application, screenshot, and power shortcuts. `Super` is the Windows key, and `Print` is the print screen key.

| Binding                         | Action                                |
| :------------------------------ | :------------------------------------ |
| `Super` + `Return`              | terminal (`foot`)                     |
| `Super` + `d`                   | launcher (`fuzzel`)                   |
| `Super` + `b`                   | browser                               |
| `Super` + `e`                   | file manager                          |
| `Super` + `Shift` + `p`         | password manager                      |
| `Super` + `Shift` + `v`         | volume control (`pavucontrol`)        |
| `Super` + `Shift` + `b`         | bluetooth manager (`blueman-manager`) |
| `Super` + `` ` ``               | dropdown terminal                     |
| `Super` + `Shift` + `w`         | rotate wallpaper                      |
| `Super` + `Shift` + `i`         | toggle the idle timer                 |
| `Super` + `Shift` + `x`         | lock screen                           |
| `Super` + `n`                   | dismiss notification                  |
| `Super` + `Shift` + `n`         | dismiss all notifications             |
| `Super` + `Control` + `n`       | restore notification                  |
| `Print`                         | screenshot full screen                |
| `Control` + `Print`             | screenshot focused window             |
| `Shift` + `Print`               | screenshot region                     |
| `Super` + `Shift` + `c`         | reload the SwayFX configuration       |
| `Super` + `Shift` + `Backspace` | power off                             |
| `Super` + `Shift` + `r`         | reboot                                |
| `Super` + `Shift` + `z`         | suspend                               |
| `Super` + `Shift` + `e`         | logout                                |

## Movement, workspaces, and layouts

Movement is Vim-style (`h`, `j`, `k`, `l`). Vim-style means the movement keys follow the layout of the Vim text editor, where `h` and `l` move left and right, and `j` and `k` move down and up. A workspace is a separate screenful of windows, like a virtual desktop. You can switch between workspaces with `Super` + `1` through `Super` + `9`, and `Super` + `0` opens workspace 10.

You can split a layout horizontally with `Super` + `o` or vertically with `Super` + `v`. You can switch between the stacking layout (`Super` + `s`), the tabbed layout (`Super` + `w`), and the split toggle (`Super` + `p`). Fullscreen is `Super` + `f`, and floating toggle is `Super` + `Shift` + `Space`.

A scratchpad is a hidden workspace that only appears when you summon it. The scratchpad gets its own pair of bindings. `Super` + `-` cycles through scratchpad windows, ignoring the dropdown terminal, and `Super` + `Shift` + `-` sends the focused window to the scratchpad.

The idle timer locks the screen after a period without input. `Super` + `Shift` + `i` toggles the timer. While it is off, the screen stays awake and unlocked until you toggle the timer back on. The script calls this state caffeine mode.

## Screenshots

`wayfreeze`, a screen-freezing helper, holds the screen still while you choose a region or window, and `grim`, the screenshot tool, takes the capture. When `wayfreeze` is not installed, the capture runs without freezing.

## Summary

You have seen how the application shortcuts are wired, with environment variables for the file manager and password manager, a wrapper script for the browser, and MIME type mappings for everything else. You have the shortcut table as a reference. Movement is Vim-style, workspaces are `Super` plus a number, and the scratchpad has its own pair of bindings.

The config file is the definitive reference. The full list of shortcuts lives in the SwayFX config template at `home/dot_config/sway/config.tmpl`.
