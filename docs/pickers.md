# Pickers

Application launching, session power actions, and clipboard history use
keyboard-controlled popups (`fuzzel` on `thinkpad`, `rofi` on `optiplex`, and
`kitty` + `fzf` for the clipboard).

Pressing any picker's keybinding a second time while it is already open closes
the picker immediately rather than spawning a duplicate window.

<figure class="screenshot">
  <img src="images/picker-dim-light.webp#only-light" alt="The application launcher centered over a dimmed Neovim window.">
  <img src="images/picker-dim.webp#only-dark" alt="The application launcher centered over a dimmed Neovim window.">
</figure>

## Application launcher (`$mod+d`)

<figure class="screenshot">
  <img src="images/picker-launcher-light.webp#only-light" alt="The application launcher open over the desktop wallpaper.">
  <img src="images/picker-launcher.webp#only-dark" alt="The application launcher open over the desktop wallpaper.">
</figure>

Searches installed `.desktop` entries (including the local TUI and toolkit
overrides in [Desktop entries](desktop-entries.md)).

`$mod+d` runs through `launcher_dim` on both machines. It places a translucent
full-screen sheet behind the menu and removes the sheet when the menu closes
(`fuzzel` on `thinkpad`, `rofi` on `optiplex`).

## Power menu (`$mod+Shift+e`)

<figure class="screenshot">
  <img src="images/picker-poweroff-light.webp#only-light" alt="A power-off confirmation dialog with yes and no options.">
  <img src="images/picker-poweroff.webp#only-dark" alt="A power-off confirmation dialog with yes and no options.">
</figure>

Presents lock, logout, reboot, and shutdown actions. Destructive actions
(logout, reboot, shutdown) open a second `Yes / No` confirmation prompt so an
accidental keypress cannot drop the session.

## Clipboard history

<figure class="screenshot no-radius">
  <img src="images/picker-clipboard-light.webp#only-light" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
  <img src="images/picker-clipboard.webp#only-dark" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
</figure>

Opens [`clipboard-picker`](https://github.com/athaurian/clipboard-picker) inside
a centered floating `kitty` window (`app_id="clipboard_term"`), showing
`cliphist` text entries and inline `kitten icat` image previews. `Enter` copies
the selected item; `Delete` or `Ctrl-D` removes it from history.
