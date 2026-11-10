#!/usr/bin/env python3
"""Launcher and power-menu figure capture and cropping."""

from __future__ import annotations

import argparse
import time
import tomllib
from pathlib import Path
from shutil import which

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    ROOT,
    RUNTIME,
    close_notifications,
    error,
    grim,
    magick,
    mode_suffix,
    palette_mode,
    run,
    run_main,
    sway,
    sway_exec,
)

DIM = tomllib.loads((ROOT / "meta" / "palette.toml").read_text())["utility"]["dim"][
    "value"
]


def crop(mode: str) -> None:
    """Crop the launcher and power-menu captures for a mode."""
    suffix = mode_suffix(mode)
    magick(
        str(CAPTURES / f"menu-launcher{suffix}.png"),
        "-crop",
        "752x498+581+307",
        "+repage",
        "-quality",
        "92",
        str(DOC_IMAGES / f"picker-launcher{suffix}.webp"),
    )
    magick(
        str(CAPTURES / f"menu-poweroff{suffix}.png"),
        "-crop",
        "752x498+581+305",
        "+repage",
        "-quality",
        "92",
        str(DOC_IMAGES / f"picker-poweroff{suffix}.webp"),
    )


def frame(mode: str) -> None:
    """Print the changed region of a launcher capture for a mode."""
    suffix = mode_suffix(mode)
    magick(
        str(CAPTURES / f"menu-launcher{suffix}.png"),
        str(CAPTURES / f"empty-{mode}.png"),
        "-compose",
        "difference",
        "-composite",
        "-crop",
        "1920x1040+0+40",
        "+repage",
        "-threshold",
        "8%",
        "-trim",
        "info:",
    )


def capture(mode: str) -> None:
    """Capture the launcher and power menu in a mode."""
    if which("fuzzel") is None:
        error("missing fuzzel")
    launcher = Path.home() / ".local/bin/launcher_dim"
    if not launcher.exists():
        error(f"missing {launcher}")
    power_control = Path.home() / ".config/sway/scripts/power_control.sh"
    if not power_control.exists():
        error(f"missing {power_control}")
    palette_mode(mode)
    sway("workspace", "3")
    try:
        close_notifications()
        sway_exec([str(launcher), DIM, "fuzzel"])
        time.sleep(1.5)
        close_notifications()
        grim(CAPTURES / f"menu-launcher{mode_suffix(mode)}.png")
        run(["pkill", "-x", "fuzzel"], check=False)
        time.sleep(0.2)
        sway_exec([str(power_control), "poweroff"])
        time.sleep(1.5)
        close_notifications()
        grim(CAPTURES / f"menu-poweroff{mode_suffix(mode)}.png")
    finally:
        run(["pkill", "-x", "fuzzel"], check=False)
        (RUNTIME / "confirm_action").unlink(missing_ok=True)
    crop(mode)


def main() -> None:
    """Run the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "crop", "frame"))
    parser.add_argument("mode", nargs="?", choices=("light", "dark"))
    args = parser.parse_args()
    if args.action in ("light", "dark"):
        if args.mode is not None:
            error(f"{args.action} does not take a mode")
        capture(args.action)
        return
    if args.mode is None:
        error(f"{args.action} requires light or dark")
    if args.action == "crop":
        crop(args.mode)
    else:
        frame(args.mode)


if __name__ == "__main__":
    run_main(main)
