# Pickers

A picker is a menu that lists items and filters them as you type. Type a few
letters and press `Enter` to choose. The pickers follow the active theme without
config changes.

Use the following table to open the picker you need:

| Shortcut          | Picker               |
| :---------------- | :------------------- |
| `Super+d`         | Launcher             |
| `Super+Control+v` | Clipboard history    |
| `Super+Control+n` | Notification history |

## Open programs with the launcher

Press `Super+d`, type part of a name, and press `Enter` to launch it.

## Reuse clipboard history

The clipboard history is an `fzf` list in a floating terminal. The clipboard
keeper stores copies from login on, so an older entry is still there after you
copy something new. Press `Super+Control+v` and follow these steps to bring one
back:

1. Type part of the entry to filter the list.
2. Check the preview pane for the full text or image.
3. Press `Enter` to copy the selected entry and close the picker.

Press `Escape` to close the picker without copying anything. If the picker is
already open, the same shortcut hides it instead of opening a second copy.

## Revisit notifications

Dismissed messages stay available for a second look. Press `Super+Control+n` to
browse them, and select an entry to show it again for five seconds. Selecting an
entry also re-displays the most recently dismissed one. When there is no
history, you get a short notice instead of an empty menu.

Three shortcuts manage notifications:

- `Super+n` dismisses one notification.
- `Super+Shift+n` dismisses all notifications.
- `Super+Control+n` opens the notification history.

## Answer confirmation menus

The power shortcuts and the login session prompt reuse a two-option `fuzzel`
menu instead of a search list. Press `Enter` to confirm the highlighted option
and `Escape` to cancel. Cancelling a power action does nothing, and cancelling
the session prompt starts fresh.
