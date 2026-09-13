# Session manager

A session is the set of windows open on the desktop, with the workspaces they
sit on, their layouts, and their open files. The session manager is a Python
program at `~/.config/sway/scripts/session_manager` that saves that state when
you leave and rebuilds it when you come back. The code lives in
`session_manager_lib/` next to it.

## Save the session

Saving is wired into the power controls in the SwayFX config. Power off, reboot,
and logout write the session to `~/.local/state/sway_session.json` first, then
the action happens. Suspend does not save, because the session keeps running
while the machine sleeps.

## Restore the session

Restoring happens at login. On startup a `fuzzel` menu asks **restore previous
session?**. Press `Enter` to choose **restore** and `Escape` to start fresh. The
menu waits 15 seconds, and no choice means nothing is restored.

The prompt only appears when there is something to bring back. You are not asked
when the state file is missing, or when the previous session was empty. The
dropdown terminal on `Super`+`` ` `` does not count on its own, since its
keybinding spawns it whenever it is missing.

## Restored content

The restore covers the following:

- Workspaces, layouts, floating windows, the scratchpad, marks, geometry, and
  fullscreen state
- Terminals with their working directories, including Neovim sessions inside
  them
- Open documents, down to the page of the PDF you were reading in zathura
- The browser, relaunched with a Helium `--restore-last-session` launch, reusing
  a running instance and topping up missing windows, then matched back to the
  windows you had
- Apps that live in the tray with no visible window, such as a minimized Vesktop

## Quality checks

If you change the code in `session_manager_lib/`, run `make check` from the
repository root. It runs the linter, the formatter, the type check, and the
whole test suite, and it stops at the first problem. The check uses `uv` to pull
in the tools it needs, so it works without a local virtual environment.
