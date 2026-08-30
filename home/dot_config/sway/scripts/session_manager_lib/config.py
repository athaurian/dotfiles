"""Paths, constants, and application profiles."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TypedDict


def _xdg_dir(env_var: str, fallback: Path) -> Path:
    value = os.environ.get(env_var)
    if value:
        return Path(value)
    return fallback


STATE_DIR = _xdg_dir("XDG_STATE_HOME", Path.home() / ".local" / "state")
STATE_FILE = STATE_DIR / "sway_session.json"
NVIM_SESSION_DIR = STATE_DIR / "nvim" / "sessions"
BACKGROUND_APPS_FILE = STATE_DIR / "sway_session_background_apps.json"

HELIUM_CONFIG_DIR = (
    _xdg_dir("XDG_CONFIG_HOME", Path.home() / ".config") / "net.imput.helium"
)

LOCK_FILE_NAME = "sway_session.lock"

# Sway scratchpad workspace name (still "__i3_scratch" in Sway).
SCRATCHPAD_WORKSPACE = "__i3_scratch"
SCRATCH_RESTORE_WORKSPACE = "__scratch_restore"

DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600


def escape_cwd(cwd: str) -> str:
    """Escape a cwd for use as a snapshot/swap filename."""
    return re.sub(r"[/\\:]+", "%", cwd)


def _float_env(name: str, default: float) -> float:
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

# Centralised timeouts previously scattered across modules.
FOOT_WAIT_TIMEOUT = 15.0
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
    "org.keepassxc.KeePassXC": "keepassxc",
    "org.pwmt.zathura": "zathura",
    "calibre-gui": "calibre",
    "calibre-ebook-viewer": "ebook-viewer",
}
