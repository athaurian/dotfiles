# Keybindings

This page describes the keyboard shortcuts in this setup and how they are wired up. It covers what each shortcut does, why some depend on environment variables and wrapper scripts, and where to look for the definitive reference. It is written for people who are new to this kind of setup, so every term is defined the first time it appears.

## Background

SwayFX is a Wayland compositor, which is the program that draws your windows on the screen and positions them. A keybinding is a shortcut, a combination of keys that triggers an action. The config is written for SwayFX, and most shortcuts use the `Super` key, which is the Windows key on most keyboards.

This page has two parts. The first part covers how the shortcuts are wired up, because some of them call scripts and read environment variables rather than launching programs directly. The second part lists the shortcuts in a reference table, with the movement and layout controls explained in the following section.

## How application shortcuts are wired

### Environment variables

An _environment variable_ is a named value that your shell and the programs you launch can read. The SwayFX config uses two of them for the file manager and password manager, named `FILEMANAGER` and `PASSWORD_MANAGER`.

If left unset, they default to `thunar` and `keepassxc` respectively. So pressing the file manager shortcut opens whatever `FILEMANAGER` points at, or `thunar` if you did not set it.

### Wrapper scripts

The browser shortcut works slightly differently. Instead of relying solely on an environment variable, it calls a wrapper script (`wrapper_browser.sh`). A _wrapper script_ is a small program that determines which real program to run. This script respects `$BROWSER` if it is set, but if not, it falls back to the first available binary, trying `helium-browser`, then `firefox`, then `chromium`, and finally `google-chrome`.

### Default applications

When you open a link or a file from outside the file manager, for example clicking a link in a terminal or a chat app, your system must determine which program handles it. MIME types drive that choice. A _MIME type_ is a label that describes what kind of content a file holds, like PDF or HTML. The mapping from MIME types to programs lives in `mimeapps.list`:

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

Other environment variables live outside the SwayFX config.

`EDITOR` lives in the `~/.bash_profile` file, and the `WLSUNSET_*` family lives in the `~/.config/wlsunset.env` file. The `~/.config/wlsunset.env` file is machine-local, and `wlsunset-location` generates it. The `~/.bash_profile` file loads it and the wlsunset service reads it.

The SwayFX autostart script lives in the `autostart.sh` file. It imports a few session variables, such as `WAYLAND_DISPLAY` and `SWAYSOCK`, into the systemd user environment. SwayFX sets those variables in its own session, and the background services that systemd starts do not see them by default. The script copies over the ones those services need, so a GUI app launched by systemd still receives the display information it needs.

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
| `Super` + `Shift` + `w`         | next wallpaper                        |
| `Super` + `Control` + `w`       | previous wallpaper                    |
| `Super` + `Shift` + `i`         | toggle the idle timer                 |
| `Super` + `Shift` + `x`         | lock screen                           |
| `Super` + `n`                   | dismiss notification                  |
| `Super` + `Shift` + `n`         | dismiss all notifications             |
| `Super` + `Control` + `n`       | restore notification                  |
| `Super` + `Control` + `v`       | clipboard history picker              |
| `Print`                         | screenshot full screen                |
| `Control` + `Print`             | screenshot focused window             |
| `Shift` + `Print`               | screenshot region                     |
| `Super` + `Shift` + `c`         | reload the SwayFX configuration       |
| `Super` + `Shift` + `Backspace` | power off                             |
| `Super` + `Shift` + `r`         | reboot                                |
| `Super` + `Shift` + `z`         | suspend                               |
| `Super` + `Shift` + `e`         | logout                                |

## Movement, workspaces, and layouts

Movement is Vim style (`h`, `j`, `k`, `l`). Vim style means the movement keys follow the layout of the Vim text editor, where `h` and `l` move left and right, and `j` and `k` move down and up. A workspace is a separate screenful of windows, like a virtual desktop. You can switch between workspaces with `Super` + `1` through `Super` + `9`, and `Super` + `0` opens workspace 10.

You can split a layout horizontally with `Super` + `o` or vertically with `Super` + `v`. To change the container shape, switch between the stacking layout (`Super` + `s`), the tabbed layout (`Super` + `w`), and the split toggle (`Super` + `p`). Fullscreen is `Super` + `f`, and floating toggle is `Super` + `Shift` + `Space`.

A scratchpad is a hidden workspace that only appears when you summon it. The scratchpad gets its own pair of bindings. `Super` + `-` cycles through scratchpad windows, ignoring the dropdown terminal and the clipboard picker, and `Super` + `Shift` + `-` sends the focused window to the scratchpad. `Super` + `Control` + `v` toggles the clipboard history picker in and out of the scratchpad. Press `Enter` to copy the selected entry and close the picker. Press `Escape` to close it without copying.

The idle timer locks the screen after a period without input. `Super` + `Shift` + `i` toggles the timer. While it is off, the screen stays awake and unlocked until you toggle the timer back on. The script calls this state caffeine mode.

The full list of shortcuts lives in the SwayFX config template at the `home/dot_config/sway/config.tmpl` file.

## Screenshots

`wayfreeze`, a screen-freezing helper, holds the screen still while you choose a region or window, and `grim`, the screenshot tool, takes the capture. When `wayfreeze` is not installed, the capture runs without freezing.
