# Pickers

Trigger the `$mod+d` keybind to open the application launcher, fuzzel on
`thinkpad` and rofi on `optiplex`.

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

Each power shortcut opens a confirmation menu in the same picker before it runs.

| Binding                | Action    |
| ---------------------- | --------- |
| `$mod+Shift+BackSpace` | Power off |
| `$mod+Shift+r`         | Reboot    |
| `$mod+Shift+z`         | Suspend   |
| `$mod+Shift+e`         | Log out   |

Press `Return` to confirm or `Esc` to cancel.

## Clipboard history

The clipboard history is an `fzf` list in a floating terminal. Press
`$mod+Ctrl+v` to open it. Type part of an entry to filter the list. The preview
pane shows the full text or image of the highlighted entry. Press `Return` to
copy it back to the clipboard and close the picker. Press `Esc` to close the
picker without copying.

If the picker is already open, the same shortcut hides it instead of opening a
second copy.

This only works on `thinkpad`. The history comes from `cliphist`, which watches
the Wayland clipboard. Copying something new does not remove the older entries,
so you can bring one back later. The history keeps up to 750 entries and drops
the oldest ones after that.
