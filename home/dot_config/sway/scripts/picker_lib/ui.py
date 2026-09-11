"""Provides launcher helpers for fuzzel dmenu mode and fzf pickers."""

from __future__ import annotations

import os
import shutil
import subprocess

FUZZEL_PROMPT_HISTORY = "󰂚 "
FZF_PROMPT_CLIPBOARD = " "

# Fuzzel shows this many rows when no explicit --lines is given. Dmenu
# prompts pass an explicit --lines capped here, so short lists render
# without empty rows while long lists keep the familiar scrolled height.
FUZZEL_MAX_LINES = 15


def have(cmd: str) -> bool:
    """Checks whether ``cmd`` is available on PATH."""
    return shutil.which(cmd) is not None


def run_fuzzel(lines: list[str], *, prompt: str, placeholder: str) -> str | None:
    """Shows ``lines`` in fuzzel dmenu mode and returns the full selected line.

    The menu is anchored to the screen center and sized to the input:
    ``--lines`` is the input length capped at ``FUZZEL_MAX_LINES``, so a
    short list shows no empty rows. Ids stay visible while ``--match-nth=2``
    keeps them out of search and ``--tabs=2`` keeps the id column narrow.
    Cancellation and empty selections return None.
    """
    lines_arg = str(max(1, min(len(lines), FUZZEL_MAX_LINES)))
    try:
        result = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                "--anchor=center",
                "--lines",
                lines_arg,
                "--match-nth=2",
                "--tabs=2",
                "--prompt",
                prompt,
                "--placeholder",
                placeholder,
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


def relaunch_in_foot(argv: list[str]) -> bool:
    """Re-executes ``argv`` inside a floating foot picker window.

    Returns False when foot is unavailable. Uses ``os.exec`` so the caller
    process is replaced and no wrapper lingers.
    """
    foot = shutil.which("foot")
    if foot is None:
        return False
    os.execvp(foot, [foot, "--app-id=foot_clipboard", "-e", *argv])
    return True  # pragma: no cover - execvp only returns on failure
