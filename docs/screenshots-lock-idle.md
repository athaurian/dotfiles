# Screenshots, lock, and idle

This page explains captures, the lock screen, and the idle timer. It assumes you are comfortable pressing shortcuts in Sway and nothing else.

## Take a screenshot

Pick what to capture with the shortcut in the following table.

| Shortcut            | Captures            |
| :------------------ | :------------------ |
| `Print`             | The full screen     |
| `Control` + `Print` | The focused window  |
| `Shift` + `Print`   | A region you select |

A _focused window_ is the window that receives keyboard input. When screen freezing is available, the screen holds still while you select. After the capture, the image opens for annotation. When the annotation tool is missing, the image goes to the clipboard instead.

## Lock the screen

Press `Super` + `Shift` + `x` to lock the screen. The lock shows your blurred desktop as its background and quiets notifications, including script notices. Unlocking brings back the notification state you had before, so do not disturb stays on when it was on.

The lock uses the `swaylock` binary. That binary comes from `swaylock-effects` when that package is installed, and from the plain `swaylock` package otherwise.

## Pause the idle timer

The idle timer locks the screen after a period without input. Press `Super` + `Shift` + `i` to toggle it. While it is off, the screen stays awake and unlocked until you toggle it back on. The notice calls this state caffeine mode.
