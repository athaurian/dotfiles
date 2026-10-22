"""Shared helpers for the clipboard picker.

Architecture boundary: this package owns *content* (list, render, pick,
copy). Window *lifecycle* (spawning terminals, toggling scratchpad
visibility) belongs to the window-manager toggle script, which is the
only place that may issue compositor IPC on the picker's behalf. The
single exception is ``ui.relaunch_in_kitty``, which execs kitty so fzf
has a terminal. Clipboard storage is selected in ``backend`` so an X11
backend can be added without touching the picker.
"""
