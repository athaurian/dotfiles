#!/usr/bin/env python3
"""Capture or convert the lock-screen figures."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    close_notifications,
    error,
    magick,
    mode_suffix,
    palette_mode,
    run_main,
    sway,
)


def convert(mode: str) -> None:
    magick(
        str(CAPTURES / f"lock-{mode}.png"),
        "-quality",
        "92",
        str(DOC_IMAGES / f"lock{mode_suffix(mode)}.webp"),
    )


def capture(mode: str) -> None:
    lock_script = Path.home() / ".config/sway/scripts/lock.sh"
    if not lock_script.exists():
        error(f"missing {lock_script}")
    palette_mode(mode)
    sway("workspace", "3")
    close_notifications()
    raw = CAPTURES / f"lock-{mode}.png"
    shooter = subprocess.Popen(
        [
            "sh",
            "-c",
            f"sleep 8; exec grim {shlex.quote(str(raw))}",
        ]
    )
    try:
        subprocess.run(
            [
                str(lock_script),
                "--timestr",
                "18:10",
                "--datestr",
                "Mon, 19 Oct",
            ],
            check=True,
        )
        if shooter.wait() != 0:
            error("lock-screen grim failed")
    finally:
        if shooter.poll() is None:
            shooter.terminate()
    convert(mode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "convert"))
    parser.add_argument("mode", nargs="?", choices=("light", "dark"))
    args = parser.parse_args()
    if args.action in ("light", "dark"):
        if args.mode is not None:
            error(f"{args.action} does not take a mode")
        capture(args.action)
        return
    if args.mode is None:
        error("convert requires light or dark")
    convert(args.mode)


if __name__ == "__main__":
    run_main(main)
