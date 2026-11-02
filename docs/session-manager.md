# Session manager

This is my favorite part of my setup, and also the most complex.

The session manager saves my desktop session when I leave and rebuilds it at
login. What does that actually mean?

When I shut down, reboot, or log out, it records the running applications, their
window positions, and their workspaces in `~/.local/state/sway_session.json`. At
login, it starts or reuses each supported application and puts its window back
on the saved workspace and at the saved position. Think of it as suspend, except
the session survives a full shutdown.

At login, a `fuzzel` prompt offers to restore the previous session. Press
`Enter` to restore that session. Press `Escape` to start fresh, or let the
prompt time out. The prompt only appears when the saved session has something
worth restoring.

See the [session-manager README](https://github.com/athaurian/session-manager)
for the commands and the full list of what comes back and what does not.
