"""Background app detection and restore (for example, minimized Vesktop)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from .config import BACKGROUND_APPS_FILE, detect_backend
from .ipc import matching_window_ids, matching_window_ids_in_tree
from .proc_cache import ProcCache

log = logging.getLogger("session_manager")

_ORIGINAL_POPEN = subprocess.Popen


def detect_background_apps(
    cache: ProcCache | None = None,
    *,
    tree: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Return background apps that have no visible window."""
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


def _ensure_background_daemons(notify_user: bool = True) -> None:
    """Perform a best-effort health check for daily-use daemons.

    Log through the session_manager logger and send a notification when a
    daemon is missing.
    """
    from .logging_setup import notify

    # Skip health checks in tests via explicit opt-out.
    if os.getenv("SWAY_SESSION_SKIP_DAEMON_CHECKS") == "1":
        return
    # Skip health checks when subprocess is mocked in tests.
    if subprocess.Popen is not _ORIGINAL_POPEN:
        return

    backend = detect_backend()
    checks: list[tuple[str, list[str], str, str | None]] = [
        ("pipewire", ["pgrep", "-x", "pipewire"], "pipewire (audio)", "pipewire"),
        (
            "pipewire-pulse",
            ["pgrep", "-x", "pipewire-pulse"],
            "pipewire-pulse (audio)",
            "pipewire-pulse",
        ),
    ]
    if backend == "i3":
        # i3 starts its screen locker from the config rather than a user unit,
        # so report a missing lock process without trying to restart it.
        checks.insert(
            0,
            (
                "xss-lock",
                ["pgrep", "-x", "xss-lock"],
                "xss-lock (screen lock)",
                None,
            ),
        )
    else:
        checks.insert(
            0,
            (
                "swayidle",
                ["pgrep", "-x", "swayidle"],
                "swayidle (screen lock)",
                "swayidle",
            ),
        )

    for name, cmd, label, service in checks:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=1.0, check=False)
            if r.returncode != 0:
                msg = f"Background daemon {label} not running, attempting restart"
                log.warning(msg)
                if notify_user:
                    notify(msg, urgency="normal", timeout_ms=4000)
                if service is None:
                    continue
                try:
                    subprocess.run(
                        ["systemctl", "--user", "start", "--no-block", service],
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

    # Ensure the session target is active (covers polkit, portal, etc. via
    # autostart). i3 sessions use i3-session.target; Sway uses
    # sway-session.target.
    target = f"{backend}-session.target"
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", target],
            capture_output=True,
            timeout=1.0,
            check=False,
        )
        if r.returncode != 0:
            msg = f"{target} not active, starting"
            log.info(msg)
            if notify_user:
                notify(msg, urgency="low", timeout_ms=3000)
            subprocess.run(
                ["systemctl", "--user", "start", "--no-block", target],
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
    notify_user: bool = True,
) -> None:
    """Restore saved background apps and check desktop daemons."""
    _ensure_background_daemons(notify_user=notify_user)

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
        try:
            subprocess.Popen(
                ["vesktop", "--start-minimized"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            log.warning("Could not start vesktop: %s", exc)
            continue
        log.info("Restored vesktop --start-minimized")
        if notify_user and subprocess.Popen is _ORIGINAL_POPEN:
            from .logging_setup import notify

            notify("vesktop restored", urgency="low", timeout_ms=3000)
