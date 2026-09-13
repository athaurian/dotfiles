# Keybindings

Shortcuts live in the SwayFX config at `home/dot_config/sway/config.tmpl`. Most
use the `Super` key, which is the Windows key on most keyboards.

## Application, screenshot, and power shortcuts

The following table lists them. `Print` is the print screen key.

| Binding                 | Action                                |
| :---------------------- | :------------------------------------ |
| `Super+Return`          | Terminal (`foot`)                     |
| `Super+d`               | Launcher (`fuzzel`)                   |
| `Super+b`               | Browser                               |
| `Super+e`               | File manager                          |
| `Super+Shift+p`         | Password manager                      |
| `Super+Shift+v`         | Volume control (`pavucontrol`)        |
| `Super+Shift+b`         | Bluetooth manager (`blueman-manager`) |
| `Super`+`` ` ``         | Dropdown terminal                     |
| `Super+Shift+w`         | Next wallpaper                        |
| `Super+Control+w`       | Previous wallpaper                    |
| `Super+Shift+i`         | Toggle the idle timer                 |
| `Super+Shift+x`         | Lock screen                           |
| `Super+n`               | Dismiss notification                  |
| `Super+Shift+n`         | Dismiss all notifications             |
| `Super+Control+n`       | Notification history                  |
| `Super+Shift+d`         | Toggle do not disturb                 |
| `Super+Control+v`       | Clipboard history picker              |
| `Print`                 | Screenshot full screen                |
| `Control+Print`         | Screenshot focused window             |
| `Shift+Print`           | Screenshot region                     |
| `Super+Shift+c`         | Reload the SwayFX configuration       |
| `Super+Shift+Backspace` | Power off                             |
| `Super+Shift+r`         | Reboot                                |
| `Super+Shift+z`         | Suspend                               |
| `Super+Shift+e`         | Logout                                |

## Movement, workspaces, and layouts

Movement follows Vim style. `h`, `j`, `k`, and `l` move left, down, up, and
right, and holding `Shift` moves or sends windows instead of focusing.
Workspaces switch with `Super+1` through `Super+9`, and `Super+0` opens
workspace 10.

Splits are horizontal with `Super+o` or vertical with `Super+v`. The container
shape switches between stacking (`Super+s`), tabbed (`Super+w`), and split
toggling (`Super+p`). Fullscreen is `Super+f`, and the floating toggle is
`Super+Shift+Space`.

`Super+r` enters the resize mode, where `h`, `j`, `k`, `l`, or the arrow keys
resize the focused window and `Return` or `Escape` leaves. `Super+q` closes the
focused window, `Super+c` centers it, and `Super+Space` switches focus between
tiling and floating windows.

The scratchpad is the hidden workspace that holds parked windows. `Super+-`
cycles through scratchpad windows, ignoring the dropdown terminal and the
clipboard picker, and `Super+Shift+-` sends the focused window to the
scratchpad. `Super+Control+v` toggles the clipboard history picker in and out of
the scratchpad. Press `Enter` to copy the selected entry and close the picker,
and `Escape` to close it without copying.

The idle timer locks the screen after a period without input. `Super+Shift+i`
toggles it. For details, see
[Screenshots, lock, and idle](screenshots-lock-idle.md).

## Application shortcuts

### Environment variables

`FILEMANAGER` and `PASSWORD_MANAGER` name the file manager and password manager
shortcuts. They default to `thunar` and the `org.keepassxc.KeePassXC` desktop
entry when unset, so pressing each shortcut opens whatever its variable points
at.

### The browser wrapper

The browser shortcut calls `wrapper_browser.sh` instead of an environment
variable alone. The wrapper respects `$BROWSER` when set, and otherwise falls
back to the first available binary: `helium-browser`, then `firefox`, then
`chromium`, then `google-chrome`.

### Default applications

MIME types map content kinds to programs in `mimeapps.list`:

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

The first program on each line is preferred, and the others are fallbacks. The
`x-scheme-handler/*` lines cover URL schemes, so `http://` links open in the
browser and `discord://` links open in Vesktop. The preferred browser is Helium,
which this setup installs.

### Other environment variables

`EDITOR` lives in the `~/.bash_profile` file. The `WLSUNSET_*` family is defined
in `~/.config/wlsunset.env`, which `wlsunset-location` generates per machine and
`~/.bash_profile` loads.

The SwayFX autostart script imports session variables such as `WAYLAND_DISPLAY`
and `SWAYSOCK` into the systemd user environment. SwayFX sets those variables in
its own session, and the services systemd starts do not see them by default, so
the script copies over the ones those services need.

## Screenshots

`wayfreeze` holds the screen still while you choose a region or window, and
`grim` takes the capture. When `wayfreeze` is not installed, the capture runs
without freezing.
