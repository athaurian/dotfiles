"""Shared helpers for the clipboard and notification-history pickers.

Architecture boundary: this package owns *content* (list, render, pick,
copy). Window *lifecycle* (spawning terminals, toggling scratchpad
visibility) belongs to the shell toggle scripts, which are the only
place that may issue compositor IPC on the pickers' behalf. The single
exception is ui.relaunch_in_foot, which execs foot so fzf has a
terminal; it must never grow beyond that. (session_manager_lib owns a
native IPC client by design and is out of scope.) Enforced by `make
lint-boundary`.
"""
