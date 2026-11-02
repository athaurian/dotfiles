# Session manager

A session is the set of windows open on the desktop, with their workspaces,
layouts, and open files. The manager saves that state when you leave and
rebuilds it when you come back. It runs on `thinkpad` only, since `optiplex`
runs i3.

## Save the session

Power off, reboot, and logout write the session to
`~/.local/state/sway_session.json` before the action runs. Suspend does not
save, because the session keeps running while the machine sleeps.

## Restore the session

Restoring happens at login. A `fuzzel` menu asks **restore previous session?**.
Press `Enter` to restore and `Escape` to start fresh. The menu waits 15 seconds,
and no choice starts fresh.

The prompt only appears when there is something to bring back. It stays hidden
when the state file is missing or the previous session was empty. The dropdown
terminal on `Super`+`` ` `` does not count on its own, since its keybinding
spawns it whenever it is missing. The topgrade and clipboard terminals are not
saved at all.

## Restored content

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

If you change the code in `session_manager_lib/`, run `make check-session` from
the repository root. It runs the linter, the formatter, the type check, and the
whole test suite.
