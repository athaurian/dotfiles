# Pickers

Application launching, session power actions, and clipboard history use
keyboard-controlled popups. The launcher and power menus use the dialog program
selected for each machine. In contrast, the clipboard picker is a `kitty` window
driven by `fzf`. The
[machine comparison](../machines.md#differences-between-thinkpad-and-optiplex)
lists the full set of per-host choices.

Pressing a picker's keybinding a second time while it is open closes the picker
instead of spawning a duplicate window.

<figure class="screenshot">
  <img src="../images/picker-dim-light.webp#only-light" alt="The application launcher centered over a dimmed Neovim window.">
  <img src="../images/picker-dim.webp#only-dark" alt="The application launcher centered over a dimmed Neovim window.">
</figure>

## Application launcher (`$mod+d`)

<figure class="screenshot">
  <img src="../images/picker-launcher-light.webp#only-light" alt="The application launcher open over the desktop wallpaper.">
  <img src="../images/picker-launcher.webp#only-dark" alt="The application launcher open over the desktop wallpaper.">
</figure>

The launcher searches installed `.desktop` entries, including the local TUI and
toolkit overrides documented in [Desktop entries](desktop-entries.md).

| Binding  | Runs                                                | Confirmation |
| :------- | :-------------------------------------------------- | :----------- |
| `$mod+d` | `launcher_dim`, then the per-machine dialog program | None         |

The dimming helper places a translucent full-screen sheet behind the menu and
removes it when the menu closes.

## Power actions

<figure class="screenshot">
  <img src="../images/picker-poweroff-light.webp#only-light" alt="A power-off confirmation dialog in light mode with yes and no options.">
  <img src="../images/picker-poweroff.webp#only-dark" alt="A power-off confirmation dialog in dark mode with yes and no options.">
</figure>

Destructive session actions require confirmation. Locking is non-destructive and
is therefore immediate. The menu uses the per-machine dialog program.

| Binding                | Action    | Confirmation  |
| :--------------------- | :-------- | :------------ |
| `$mod+Shift+BackSpace` | Power off | Yes / No menu |
| `$mod+Shift+r`         | Reboot    | Yes / No menu |
| `$mod+Shift+z`         | Suspend   | Yes / No menu |
| `$mod+Shift+e`         | Log out   | Yes / No menu |
| `$mod+Shift+x`         | Lock      | None          |

## Clipboard history

<figure class="screenshot no-radius">
  <img src="../images/picker-clipboard-light.webp#only-light" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
  <img src="../images/picker-clipboard.webp#only-dark" alt="The clipboard history picker listing five entries, with the palette card previewed beside them.">
</figure>

[`clipboard-picker`](https://github.com/athaurian/clipboard-picker) opens inside
a centered floating `kitty` window. The picker renders clipboard history with
inline image previews.

| Property       | Value                            |
| :------------- | :------------------------------- |
| Window class   | `clipboard_term`                 |
| History source | `cliphist`                       |
| Image previews | Rendered inline by `kitten icat` |

Key bindings act on the selected entry.

| Binding             | Action                   |
| :------------------ | :----------------------- |
| `Enter`             | Copies the selected item |
| `Delete` / `Ctrl-D` | Removes it from history  |
