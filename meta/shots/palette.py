#!/usr/bin/env python3
"""Palette card figure rendering."""

from __future__ import annotations

import argparse

from shotlib import run_main, run_pillow


def main() -> None:
    """Render the palette card through the shared Pillow runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_pillow("palette-card.py")


if __name__ == "__main__":
    run_main(main)
