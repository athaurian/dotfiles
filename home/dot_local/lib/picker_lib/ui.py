"""Launcher helpers for the fzf clipboard picker."""

from __future__ import annotations

import os
import shutil
import subprocess

FZF_PROMPT_CLIPBOARD = " "


def have(cmd: str) -> bool:
    """Checks whether ``cmd`` is available on PATH."""
    return shutil.which(cmd) is not None


def run_fzf(
    lines: list[str], *, prompt: str, header: str, preview_cmd: str
) -> str | None:
    """Shows ``lines`` in fzf and returns the full selected line.

    Ids stay visible while ``--nth=2`` scopes search to the display text
    and ``--tabstop=2`` keeps the id column narrow. Cancellation (Esc,
    Ctrl-C) and no-match exits return None.
    """
    try:
        result = subprocess.run(
            [
                "fzf",
                "-d",
                "\t",
                "--nth=2",
                "--tabstop=2",
                f"--prompt={prompt}",
                f"--header={header}",
                "--layout=reverse",
                "--border",
                "--info=inline",
                f"--preview={preview_cmd}",
                "--preview-window=right,50%,wrap",
            ],
            input="\n".join(lines) + "\n",
            check=False,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    selected = result.stdout.strip()
    return selected or None


def relaunch_in_kitty(argv: list[str]) -> bool:
    """Re-executes ``argv`` inside a floating kitty picker window.

    Returns False when kitty is unavailable. Uses ``os.exec`` so the caller
    process is replaced and no wrapper lingers. The window title is what the
    compositor rule matches to float and mark the picker.
    """
    kitty = shutil.which("kitty")
    if kitty is None:
        return False
    os.execvp(kitty, [kitty, "--title", "clipboard_term", "-e", *argv])
    return True  # pragma: no cover - execvp only returns on failure
