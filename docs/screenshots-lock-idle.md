# Screenshots, lock, and idle

This page covers screen captures, the lock screen, and the idle timer.

## Take a screenshot

Pick what to capture with the shortcut in the following table:

| Shortcut        | Captures            |
| :-------------- | :------------------ |
| `Print`         | The full screen     |
| `Control+Print` | The focused window  |
| `Shift+Print`   | A region you select |

When screen freezing is available, the screen holds still while you select.
After the capture, the image opens for annotation, or goes to the clipboard when
the annotation tool is missing.

## Lock the screen

Press `Super+Shift+x` to lock the screen. The lock shows the blurred desktop as
its background and quiets notifications, including script notices. Unlocking
brings back the notification state you had before, so do not disturb stays on
when it was on.

The lock uses the `swaylock` binary, which comes from `swaylock-effects` when
that package is installed and from the plain `swaylock` package otherwise.

## Toggle the idle timer

The idle timer locks the screen after a period without input. Press
`Super+Shift+i` to toggle it. While it is off, the screen stays awake and
unlocked until you toggle it back on. The idle script calls this state caffeine
mode.
