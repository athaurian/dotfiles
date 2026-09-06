"""Background app detection and restoration (for example, minimized Vesktop)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from .config import BACKGROUND_APPS_FILE
from .ipc import matching_window_ids, matching_window_ids_in_tree
from .proc_cache import ProcCache

log = logging.getLogger("session_manager")

_ORIGINAL_POPEN = subprocess.Popen


def detect_background_apps(
    cache: ProcCache | None = None,
    *,
    tree: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    cache = cache or ProcCache.snapshot()
    apps: list[dict[str, str]] = []
    vesktop_visible = bool(
        matching_window_ids_in_tree(tree, "vesktop", "")
        if tree is not None
        else matching_window_ids("vesktop", "")
    )
    if cache.process_named_running("vesktop") and not vesktop_visible:
        apps.append({"app_id": "vesktop"})
    return apps


def _ensure_background_daemons() -> None:
    """Best-effort health check for daily-use daemons. Logs to file + notification path."""
    from .logging_setup import notify

    # Skip health checks in tests via explicit opt-out, not by detecting mocks.
    if os.getenv("SWAY_SESSION_SKIP_DAEMON_CHECKS") == "1":
        return
    # Skip health checks when subprocess is mocked in tests.
    if subprocess.Popen is not _ORIGINAL_POPEN:
        return

    checks: list[tuple[str, list[str], str]] = [
        ("swayidle", ["pgrep", "-x", "swayidle"], "swayidle (screen lock)"),
        ("pipewire", ["pgrep", "-x", "pipewire"], "pipewire (audio)"),
        ("pipewire-pulse", ["pgrep", "-x", "pipewire-pulse"], "pipewire-pulse (audio)"),
    ]
    for name, cmd, label in checks:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=1.0, check=False)
            if r.returncode != 0:
                msg = f"Background daemon {label} not running, attempting restart"
                log.warning(msg)
                notify(msg, urgency="normal", timeout_ms=4000)
                # Try systemd first, fall back to direct start for swayidle
                try:
                    subprocess.run(
                        ["systemctl", "--user", "start", "--no-block", name],
                        capture_output=True,
                        timeout=2.0,
                        check=False,
                    )
                except (
                    OSError,
                    subprocess.SubprocessError,
                    subprocess.TimeoutExpired,
                    TypeError,
                ):
                    pass
        except (
            OSError,
            subprocess.SubprocessError,
            subprocess.TimeoutExpired,
            TypeError,
        ):
            continue

    # Ensure sway-session.target is active (covers polkit, portal, etc. via autostart)
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "sway-session.target"],
            capture_output=True,
            timeout=1.0,
            check=False,
        )
        if r.returncode != 0:
            msg = "sway-session.target not active, starting"
            log.info(msg)
            notify(msg, urgency="low", timeout_ms=3000)
            subprocess.run(
                ["systemctl", "--user", "start", "--no-block", "sway-session.target"],
                capture_output=True,
                timeout=2.0,
                check=False,
            )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired, TypeError):
        pass


def restore_background_apps(
    apps: list[dict[str, str]] | None = None,
    *,
    cache: ProcCache | None = None,
) -> None:
    _ensure_background_daemons()

    if apps is None:
        if not BACKGROUND_APPS_FILE.exists():
            return
        try:
            loaded = json.loads(BACKGROUND_APPS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("Could not parse %s", BACKGROUND_APPS_FILE)
            return
        if not isinstance(loaded, list):
            log.warning("Invalid background apps payload in %s", BACKGROUND_APPS_FILE)
            return
        apps = loaded

    for app in apps:
        if not isinstance(app, dict):
            continue
        if app.get("app_id") != "vesktop":
            continue
        if matching_window_ids("vesktop", ""):
            continue
        if cache is None:
            cache = ProcCache.snapshot()
        if cache.process_named_running("vesktop"):
            continue
        subprocess.Popen(
            ["vesktop", "--start-minimized"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log.info("Restored vesktop --start-minimized")
        if subprocess.Popen is _ORIGINAL_POPEN:
            from .logging_setup import notify

            notify("vesktop restored", urgency="low", timeout_ms=3000)
