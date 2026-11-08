#!/usr/bin/env python3
"""Open Graph banner composition."""

from __future__ import annotations

import argparse

from shotlib import CAPTURES, DOC_IMAGES, magick, run_main

COVER = ("600x630^", "-extent", "600x630")


def compose() -> None:
    """Join the two half-width captures into the banner."""
    magick(
        "(",
        str(CAPTURES / "editor-light.png"),
        "-crop",
        "960x1008+0+36",
        "+repage",
        "-resize",
        *COVER,
        ")",
        "(",
        str(CAPTURES / "empty-dark.png"),
        "-crop",
        "960x1008+960+0",
        "+repage",
        "-resize",
        *COVER,
        ")",
        "+append",
        "+repage",
        str(DOC_IMAGES / "og.png"),
    )


def main() -> None:
    """Run the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    compose()


if __name__ == "__main__":
    run_main(main)
