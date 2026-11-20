# Theming

Press `$mod+Shift+t` at any time to toggle the desktop between dark and light
modes. The toggle updates both persistent state and the processes that retain
colors in memory.

## Live toggle behavior

The toggle flips the recorded mode and then runs the apply flow in
[Mode switch behavior](../system/palette-system.md#mode-switch-behavior). Its
five stages are not repeated here. The toggle itself performs three stages:

1. Read the current mode from `~/.local/state/palette-mode`. A missing file
   defaults to `dark`.
2. Flip the mode and run the palette apply flow from `~/.local/share/chezmoi`.
3. Update the running applications.

The GTK and Calibre updates are described in
[Applications](applications.md#theme-synchronization-hook).

A rewritten configuration file does not change a process that has already cached
the old palette in memory. The hook and the Neovim watcher are the explicit
reload actions that deliver the new colors without restarting those
applications.
