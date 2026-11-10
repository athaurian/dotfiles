# Session manager

This is my favorite part of my setup, and also the most complex.

The session manager saves my desktop session when I leave and rebuilds it at
login.

When I shut down, reboot, or log out, it records the running applications, their
window positions, and their workspaces in a state file under `~/.local/state/`.
At login, it starts or reuses each supported application and puts its window
back on the saved workspace and at the saved position. Unlike suspend, the saved
session survives a full shutdown.

At login, a picker prompt offers to restore the previous session. Press `Enter`
to restore that session. Press `Esc` to start a new session, or let the prompt
time out. The prompt appears only when the saved session isn't empty.

See the [session-manager README](https://github.com/athaurian/session-manager)
for the commands and the full list of what is restored and what is not.
