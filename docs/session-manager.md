# Session manager

This section explains what the session manager does. It covers when your desktop gets saved, when it comes back, and what comes back with it. It is written for people who are new to this kind of setup, so every term is defined the first time it appears.

## Overview

A session is the set of windows open on your desktop, with the workspaces they sit on, their layouts, and their open files. A workspace is a separate screenful of windows, like a virtual desktop. The session manager is a small Python program that saves that state when you leave and rebuilds it when you come back. It lives at `~/.config/sway/scripts/session_manager`, with the real code in `session_manager_lib/` next to it.

## When the session is saved

Saving is wired into the power controls in the SwayFX config. When you log out, power off, or reboot, the session is saved to `~/.local/state/sway_session.json` first, then the action happens. Suspend does not save, because the session keeps running while the machine sleeps.

## When the session is restored

Restoring happens at login. On startup you get a `swaynag` bar, the confirmation prompt that ships with Sway. It asks **restore previous session?**, with buttons for **Restore** and **Start fresh**. Choose **Restore** and the manager relaunches your apps and rebuilds the desktop. The prompt waits about a minute. If you make no choice, nothing is restored. Silence counts as a no.

The prompt only appears when there is something to bring back. You are not asked at all when the state file is missing, or when the previous session was empty with no windows, scratchpad entries, or background apps. The dropdown terminal, the hidden one on `Super` + `` ` ``, does not count on its own, since its keybind spawns it whenever it is missing.

## What is restored

The restore covers the following:

- Workspaces, layouts, floating windows, the scratchpad, marks, geometry, and fullscreen state.
- Terminals with their working directories, including Neovim sessions inside them.
- Open documents, down to the page of the PDF you were reading in zathura, the PDF reader.
- The browser, restored with a single launch of Helium's `--restore-last-session` flag, then matched back to the windows you had.
- Apps that live in the tray, the panel's icon area, with no visible window, like a minimized Vesktop, the Discord client.

The scratchpad is the hidden workspace that holds parked windows, and marks are labels attached to individual windows.

## Quality checks

If you change the code in `session_manager_lib/`, there is a quality gate you can run to verify nothing broke. The repository `Makefile` has a `check` target for it. It runs the linter, the formatter, a type check, and the whole test suite of the session manager library, and it stops at the first problem it finds.

Run it from the repository root:

    make check

The gate uses `uv`, a fast Python package manager, to pull in the tools it needs, so it works without a local virtual environment.
