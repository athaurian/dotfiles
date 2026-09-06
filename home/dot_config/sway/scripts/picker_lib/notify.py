"""Desktop notification helper that wraps ``notify-send``."""

from __future__ import annotations

import subprocess


def send(
    summary: str,
    body: str = "",
    *,
    app_name: str = "picker",
    urgency: str = "low",
    timeout_ms: int = 3000,
) -> None:
    """Shows a desktop notification, silently skipping when ``notify-send`` is missing."""
    args = [
        "notify-send",
        "-a",
        app_name,
        "-u",
        urgency,
        "-t",
        str(timeout_ms),
    ]
    if body:
        args += [summary, body]
    else:
        args += [summary]
    try:
        subprocess.run(args, check=False, capture_output=True)
    except (FileNotFoundError, OSError):
        pass
