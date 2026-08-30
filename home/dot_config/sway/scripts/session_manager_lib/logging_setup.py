"""Logging and desktop notification helpers."""

from __future__ import annotations

import logging
import subprocess

log = logging.getLogger("session_manager")

_last_notify_id: str | None = None
_notify_send_missing = False


def notify(msg: str, *, timeout_ms: int = 3000, urgency: str = "low") -> None:
    global _last_notify_id, _notify_send_missing
    if _notify_send_missing:
        return
    args = [
        "notify-send",
        "-u",
        urgency,
        "-t",
        str(timeout_ms),
        "-p",
        "󰁯 session manager",
        msg,
    ]
    if _last_notify_id is not None:
        args.extend(["-r", _last_notify_id])
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        _notify_send_missing = True
        log.info("notify-send not found; desktop notifications disabled")
        return
    except (OSError, TypeError, ValueError) as exc:
        log.debug("notify-send failed: %s", exc)
        return
    nid = result.stdout.strip()
    _last_notify_id = nid if (nid and nid.isdigit()) else None
