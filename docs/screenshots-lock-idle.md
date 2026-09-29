# Screenshots, lock, and idle

This page covers screen captures, the lock screen, and the idle timer. The three
paths differ per machine.

## Take a screenshot

| Shortcut        | thinkpad (Sway) | optiplex (i3)               |
| --------------- | --------------- | --------------------------- |
| `Print`         | Full screen     | Full screen                 |
| `Shift+Print`   | Select a region | Select a region (flameshot) |
| `Control+Print` | —               | The focused window          |

On thinkpad the screen freezes (wayfreeze) while you select, grim captures the
region, and the result opens in satty for annotation. The raw capture reaches
the clipboard immediately, and whatever you save in satty is copied there as
well; without satty the raw capture is what you get.

On optiplex flameshot does the work: `Print` grabs the full screen,
`Control+Print` the focused window, and `Shift+Print` opens flameshot's own
selection window. Each path copies the result to the clipboard.

## Lock the screen

`$mod+Shift+x` locks the machine through that config's `lock.sh`:

- **thinkpad** runs swaylock with the blurred desktop as its background.
- **optiplex** runs i3lock (i3lock-color) over a blurred capture of the screen.

Both pause notifications while locked and restore the previous do-not-disturb
state on unlock, so a quiet session stays quiet across a lock.

## Toggle the idle timer

The idle timer locks the screen after a period without input. Press
`$mod+Shift+i` to toggle it: while it is off, the screen stays awake and
unlocked until you toggle it back on.

- **thinkpad** runs swayidle as two units, one for the unlocked state and one
  for the locked state, which the lock script switches between. A warning
  appears after 20 seconds and the screen locks after 30.
- **optiplex** uses the native X11 path: `xset s 20 10` arms the screensaver
  (warning at 20 seconds, lock ten seconds later), `xss-lock` runs `lock.sh`
  when it triggers, and DPMS blanks the outputs after 90 seconds. There is no
  idle suspend on this machine.

Before the lock fires, the idle helpers fade the screen and show a short notice,
so the warning survives a compositor restart.
