"""Paths, constants, and application profiles."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TypedDict


def _xdg_dir(env_var: str, fallback: Path) -> Path:
    """Return an XDG directory from the environment, or a fallback."""
    value = os.environ.get(env_var)
    if value:
        return Path(value)
    return fallback


def detect_backend() -> str:
    """Return the window manager backend in use: ``"i3"`` or ``"sway"``.

    Sway and i3 share the i3 IPC protocol, but they expose different window
    identities and use separate state files. An explicit
    ``SESSION_MANAGER_BACKEND`` wins so tests and nested sessions can pin the
    choice. Otherwise the compositor's socket and desktop environment decide.
    """
    override = os.environ.get("SESSION_MANAGER_BACKEND", "").strip().lower()
    if override in ("i3", "sway"):
        return override

    has_sway = bool(os.environ.get("SWAYSOCK"))
    has_i3 = bool(os.environ.get("I3SOCK"))
    if has_sway != has_i3:
        return "sway" if has_sway else "i3"

    desktops = " ".join(
        os.environ.get(name, "")
        for name in ("XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "XDG_SESSION_DESKTOP")
    ).lower()
    if "sway" in desktops:
        return "sway"
    if "i3" in desktops:
        return "i3"

    if os.environ.get("WAYLAND_DISPLAY"):
        return "sway"
    if os.environ.get("DISPLAY"):
        return "i3"
    return "sway"


BACKEND = detect_backend()

STATE_DIR = _xdg_dir("XDG_STATE_HOME", Path.home() / ".local" / "state")
SWAY_STATE_FILE = STATE_DIR / "sway_session.json"
I3_STATE_FILE = STATE_DIR / "i3_session.json"
STATE_FILE = I3_STATE_FILE if BACKEND == "i3" else SWAY_STATE_FILE
NVIM_SESSION_DIR = STATE_DIR / "nvim" / "sessions"
SWAY_BACKGROUND_APPS_FILE = STATE_DIR / "sway_session_background_apps.json"
I3_BACKGROUND_APPS_FILE = STATE_DIR / "i3_session_background_apps.json"
BACKGROUND_APPS_FILE = (
    I3_BACKGROUND_APPS_FILE if BACKEND == "i3" else SWAY_BACKGROUND_APPS_FILE
)

HELIUM_CONFIG_DIR = (
    _xdg_dir("XDG_CONFIG_HOME", Path.home() / ".config") / "net.imput.helium"
)

LOCK_FILE_NAME = f"{BACKEND}_session.lock"

# Both window managers keep the i3 scratchpad workspace name.
SCRATCHPAD_WORKSPACE = "__i3_scratch"
SCRATCH_RESTORE_WORKSPACE = "__scratch_restore"

DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600

# A floating window that has just started asks Sway for its own size, and
# that request can land after the restore's resize and undo it. Apply the
# geometry again after this delay, once the window has settled, so the
# restored size sticks.
FLOAT_GEOMETRY_RETRY_DELAY = 0.4


def escape_cwd(cwd: str) -> str:
    """Escape a cwd for use as a snapshot or swap filename.

    Percent signs are escaped before separators so a directory whose name
    contains ``%`` cannot map to the same filename as a different directory
    whose separator became ``%``.
    """
    return re.sub(r"[/\\:]+", "%", cwd.replace("%", "%25"))


def _float_env(name: str, default: float) -> float:
    """Read a float environment variable, falling back on invalid input."""
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


IPC_REQUEST_TIMEOUT = _float_env("SWAY_SESSION_IPC_REQUEST_TIMEOUT", 1.0)

CALIBRE_DB = Path.home() / "Library" / "metadata.db"
CALIBRE_CONFIG = Path.home() / ".config" / "calibre" / "viewer-webengine.json"

MANAGER_SESSIONOPTIONS = (
    "buffers,curdir,folds,globals,help,tabpages,winsize,winpos,localoptions,skiprtp"
)


class AppProfile(TypedDict):
    """Launch and matching behaviour for one supported application."""

    settle: float
    reject_floating: bool
    timeout: float
    singleton: bool


APP_PROFILES: dict[str, AppProfile] = {
    "vesktop": {
        "settle": 1.2,
        "reject_floating": True,
        "timeout": 30.0,
        "singleton": True,
    },
    "helium": {
        "settle": 0.3,
        "reject_floating": False,
        "timeout": 30.0,
        "singleton": False,
    },
    "thunar": {
        "settle": 0.3,
        "reject_floating": False,
        "timeout": 15.0,
        "singleton": False,
    },
    "mpv": {
        "settle": 0.3,
        "reject_floating": False,
        "timeout": 15.0,
        "singleton": False,
    },
    "org.pwmt.zathura": {
        "settle": 0.3,
        "reject_floating": False,
        "timeout": 15.0,
        "singleton": False,
    },
    "calibre-gui": {
        "settle": 1.0,
        "reject_floating": False,
        "timeout": 30.0,
        "singleton": True,
    },
    "calibre-ebook-viewer": {
        "settle": 0.3,
        "reject_floating": False,
        "timeout": 20.0,
        "singleton": False,
    },
}

DEFAULT_APP_PROFILE: AppProfile = {
    "settle": 0.3,
    "reject_floating": False,
    "timeout": 20.0,
    "singleton": False,
}

# Shared timeouts for the waits other modules perform.
TERMINAL_WAIT_TIMEOUT = 15.0
APP_WAIT_TIMEOUT = 15.0
ZATHURA_DBUS_TIMEOUT = 2.0
ZATHURA_GOTO_PAGE_DEADLINE = 5.0
NVIM_RPC_TIMEOUT = 10.0
IPC_SUBSCRIBE_TIMEOUT = 5.0
WATCHER_JOIN_TIMEOUT = 1.0
WINDOW_SETTLE_POLL_INTERVAL = 0.1
HELIUM_TITLE_GRACE_PERIOD = 2.5
HELIUM_ASSIGNMENT_TIMEOUT = 5.0
HELIUM_WINDOW_STALL_TIMEOUT = 3.0

APP_ID_COMMANDS: dict[str, str] = {
    "helium": "helium-browser",
    "vesktop": "vesktop",
    "thunar": "thunar",
    "mpv": "mpv",
    "blueman-manager": "blueman-manager",
    "pavucontrol": "pavucontrol",
    # Qt5 wrapper desktop entry, which pins qt5ct.
    "org.keepassxc.KeePassXC": "gtk-launch org.keepassxc.KeePassXC",
    "org.pwmt.zathura": "zathura",
    "calibre-gui": "calibre",
    "calibre-ebook-viewer": "ebook-viewer",
}

# X11 exposes only WM_CLASS (class/instance), while Wayland apps have an
# app_id. i3 reports class names such as "Thunar" or "Helium", so map the
# common ones onto the lower-case identifiers used by Sway and the handlers.
APP_ID_ALIASES: dict[str, str] = {
    "thunar": "thunar",
    "zathura": "org.pwmt.zathura",
    "org.pwmt.zathura": "org.pwmt.zathura",
    "helium": "helium",
    "helium-browser": "helium",
    "calibre": "calibre-gui",
    "calibre-gui": "calibre-gui",
    "calibre-ebook-viewer": "calibre-ebook-viewer",
    "kitty": "kitty",
    "mpv": "mpv",
    "vesktop": "vesktop",
    "blueman-manager": "blueman-manager",
    "pavucontrol": "pavucontrol",
    "org.keepassxc.keepassxc": "org.keepassxc.KeePassXC",
    "keepassxc": "org.keepassxc.KeePassXC",
}


def canonical_app_id(value: str) -> str:
    """Normalize an app_id or WM_CLASS to the identifier used in state files."""
    value = (value or "").strip()
    if not value:
        return ""
    return APP_ID_ALIASES.get(value.lower(), value.lower())


# The drop terminal runs under this X11 WM_CLASS instance, which is what the
# window manager's `for_window` rule keys on. Both the launcher and the save-side
# classifier share it so a restored drop terminal stays recognisable.
DROP_TERMINAL_INSTANCE = "scratchpad_term"

# Titles the transient helper terminals use. They come and go on their own, so
# saving them would resurrect scratch helpers on the next restore.
TRANSIENT_TERMINAL_TITLES = frozenset(("topgrade_term", "clipboard_term"))
DROP_TERMINAL_TITLE = "drop_term"
