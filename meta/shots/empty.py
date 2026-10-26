#!/usr/bin/env python3
"""Capture or compose the empty-desktop hero pair."""

from __future__ import annotations

import argparse
import time

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    close_notifications,
    grim,
    palette_mode,
    run_main,
    run_pillow,
    sway,
)


def capture(mode: str) -> None:
    palette_mode(mode)
    sway("workspace", "3")
    close_notifications()
    time.sleep(10)
    grim(CAPTURES / f"empty-{mode}.png")


def compose() -> None:
    run_pillow(
        "hero.py",
        str(CAPTURES / "empty-light.png"),
        str(CAPTURES / "empty-dark.png"),
        "-o",
        str(DOC_IMAGES / "hero-empty.webp"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "compose"))
    args = parser.parse_args()
    if args.action == "compose":
        compose()
    else:
        capture(args.action)


if __name__ == "__main__":
    run_main(main)
