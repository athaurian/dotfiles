#!/usr/bin/env python3
"""Render the palette card figure."""

from __future__ import annotations

import argparse

from shotlib import run_main, run_pillow


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_pillow("palette-card.py")


if __name__ == "__main__":
    run_main(main)
