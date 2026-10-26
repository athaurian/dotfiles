#!/usr/bin/env python3
"""Crop the Discord profile-card figures from full-screen captures."""

from __future__ import annotations

import argparse

from shotlib import CAPTURES, DOC_IMAGES, crop_round, run_main


def crop(mode: str) -> None:
    if mode == "dark":
        box = "432x158+960+281"
        edge = "17181b"
        background = "050505"
        suffix = ""
    else:
        box = "432x160+960+281"
        edge = "eaeaec"
        background = "f3efec"
        suffix = "-light"
    crop_round(
        CAPTURES / f"discord-{mode}.png",
        DOC_IMAGES / f"neovim-discord{suffix}.webp",
        crop=box,
        radius=12,
        edge=edge,
        background=background,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("dark", "light", "compose"))
    args = parser.parse_args()
    if args.action == "compose":
        crop("dark")
        crop("light")
    else:
        crop(args.action)


if __name__ == "__main__":
    run_main(main)
