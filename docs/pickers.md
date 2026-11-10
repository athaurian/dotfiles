# Pickers

Press `$mod+d` to open the application launcher: fuzzel on `thinkpad` and rofi
on `optiplex`. On `thinkpad`, the rest of the screen is dim while the launcher
is open. Press `$mod+d` again to close the launcher.

<div class="image-pair">
  <figure>
    <img src="images/picker-launcher-light.webp#only-light" alt="The application launcher open over the desktop wallpaper.">
    <img src="images/picker-launcher.webp#only-dark" alt="The application launcher open over the desktop wallpaper.">
  </figure>
  <figure>
    <img src="images/picker-poweroff-light.webp#only-light" alt="A power-off confirmation dialog with yes and no options.">
    <img src="images/picker-poweroff.webp#only-dark" alt="A power-off confirmation dialog with yes and no options.">
  </figure>
</div>

Each of these bindings opens a confirmation menu in the same picker before the
action runs.

| Binding                | Action    |
| ---------------------- | --------- |
| `$mod+Shift+BackSpace` | Power off |
| `$mod+Shift+r`         | Reboot    |
| `$mod+Shift+z`         | Suspend   |
| `$mod+Shift+e`         | Log out   |

Press `Enter` to confirm or `Esc` to cancel.

## Clipboard history

Clipboard history appears as an `fzf` list in a floating terminal. Here's how to
use the picker:

1. Press `$mod+Ctrl+v` to open the picker.
2. Type part of an entry to filter the list. The preview pane shows the full
   text or image of the highlighted entry.
3. Press `Enter` to copy the highlighted entry back to the clipboard and close
   the picker, or press `Esc` to close the picker without copying anything.

If the picker is already open, the same binding hides it instead of opening
another instance.

<figure class="screenshot no-radius">
  <img src="images/picker-clipboard-light.webp#only-light" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
  <img src="images/picker-clipboard.webp#only-dark" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
</figure>

I only have this on `thinkpad`, where `cliphist` stores Wayland clipboard
entries. Copying something new doesn't remove the older entries, so you can
still bring one back later.
