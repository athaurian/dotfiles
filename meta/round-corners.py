"""Crop a screenshot to a window box with rounded corners.

The captures show the desktop in the corners around the window. The docs site
shows transparent pixels as black, so this fills the corners with the page
background color instead.

The mask is anti-aliased so the curve stays smooth. Pixels along the boundary
are painted with the window's edge color first, so the curve fades from the
window edge to the page background instead of carrying desktop colors.
"""

import argparse
import re

import numpy as np
from PIL import Image


def parse_box(value):
    match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError("expected WxH+X+Y")
    width, height, left, top = map(int, match.groups())
    return left, top, left + width, top + height


def parse_color(value):
    digits = value.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", digits):
        raise argparse.ArgumentTypeError("expected a six-digit hex color")
    return tuple(int(digits[index : index + 2], 16) for index in (0, 2, 4))


def rounded_alpha(width, height, radius):
    ys, xs = np.mgrid[0:height, 0:width]
    px, py = xs + 0.5, ys + 0.5
    half_x, half_y = width / 2.0, height / 2.0
    qx = np.abs(px - half_x) - (half_x - radius)
    qy = np.abs(py - half_y) - (half_y - radius)
    distance = (
        np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
        + np.minimum(np.maximum(qx, qy), 0.0)
        - radius
    )
    return np.clip(0.5 - distance, 0.0, 1.0)


def render(source, output, box, radius, edge, background, quality):
    left, top, right, bottom = box
    image = Image.open(source).convert("RGB")
    crop = np.asarray(image.crop((left, top, right, bottom))).astype(np.float64)
    height, width, _ = crop.shape
    alpha = rounded_alpha(width, height, radius)
    painted = np.where((alpha < 1.0)[..., None], np.array(edge), crop)
    composed = painted * alpha[..., None] + np.array(background) * (
        1.0 - alpha[..., None]
    )
    Image.fromarray(np.clip(np.rint(composed), 0, 255).astype(np.uint8)).save(
        output, "WEBP", quality=quality
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--crop", required=True, type=parse_box, metavar="WxH+X+Y")
    parser.add_argument("--radius", required=True, type=float)
    parser.add_argument("--edge", required=True, type=parse_color, metavar="HEX")
    parser.add_argument("--background", required=True, type=parse_color, metavar="HEX")
    parser.add_argument("--quality", type=int, default=92)
    arguments = parser.parse_args()
    render(
        arguments.source,
        arguments.output,
        arguments.crop,
        arguments.radius,
        arguments.edge,
        arguments.background,
        arguments.quality,
    )


if __name__ == "__main__":
    main()
