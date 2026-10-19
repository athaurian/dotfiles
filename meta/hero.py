#!/usr/bin/env python3
"""Combine a light and dark desktop screenshot pair into one diagonal split.

Both inputs must share the same dimensions. The divider runs from a point on
the top edge to a point on the bottom edge, by default three quarters of the
width across the top and one quarter across the bottom. The dark screenshot
fills the area above the divider and the light screenshot fills the area
below it; the cut is anti-aliased so the halves meet cleanly along the
diagonal, with no separator line drawn.

The wallpapers behind the two modes do not have to match: the composite is a
comparison, not a preview.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

QUALITY = 82
MASK_SCALE = 4


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hero",
        description="Combine light and dark desktop screenshots into a "
        "diagonal split, dark above the divider and light below it.",
    )
    parser.add_argument("light", type=Path, help="light mode screenshot")
    parser.add_argument("dark", type=Path, help="dark mode screenshot")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="output image (a .webp or .png suffix picks the format)",
    )
    parser.add_argument(
        "--top-x",
        type=float,
        default=0.75,
        help="divider's top endpoint as a fraction of the width from the "
        "left (default: 0.75)",
    )
    parser.add_argument(
        "--bottom-x",
        type=float,
        default=0.25,
        help="divider's bottom endpoint as a fraction of the width from the "
        "left (default: 0.25)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=0,
        help=f"output width, 0 keeps the source size (default: 0)",
    )
    return parser.parse_args(argv)


def composite(args: argparse.Namespace) -> Image.Image:
    light = Image.open(args.light).convert("RGB")
    dark = Image.open(args.dark).convert("RGB")
    if light.size != dark.size:
        raise SystemExit(
            f"error: screenshots differ in size: {light.width}x{light.height} "
            f"and {dark.width}x{dark.height}"
        )

    width, height = light.size
    top_x = round(width * MASK_SCALE * max(0.0, min(1.0, args.top_x)))
    bottom_x = round(width * MASK_SCALE * max(0.0, min(1.0, args.bottom_x)))

    mask = Image.new("L", (width * MASK_SCALE, height * MASK_SCALE), 0)
    ImageDraw.Draw(mask).polygon(
        [(0, 0), (top_x, 0), (bottom_x, height * MASK_SCALE), (0, height * MASK_SCALE)],
        fill=255,
    )
    mask = mask.resize((width, height), Image.Resampling.BILINEAR)
    image = Image.composite(dark, light, mask)

    if 0 < args.width < image.width:
        scaled = round(image.height * args.width / image.width)
        image = image.resize((args.width, scaled), Image.Resampling.LANCZOS)
    return image


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    image = composite(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".webp":
        image.save(args.output, "WEBP", quality=QUALITY, method=6)
    else:
        image.save(args.output)
    print(f"{image.width}x{image.height} -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
