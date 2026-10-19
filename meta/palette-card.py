#!/usr/bin/env python3
"""Render the palette swatch card in docs/images/palette.webp.

Reads the derived palette from meta/palette.py so the light neutral ramp and
the derived tints come from the same code path that generates the desktop
data. Run it with Pillow available:

    uv run --with pillow python3 meta/palette-card.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import palette  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "docs" / "images" / "palette.webp"

WIDTH = 1600
SCALE = 2
PAD = 44

HEADER_SIZE = 30
HEADER_HEIGHT = 34
HEADER_GAP = 20

SECTION_SIZE = 16
SECTION_HEIGHT = 21
GROUP_TOP = 12

CIRCLE_DIAMETER = 76
CIRCLE_GAP = 32

NAME_SIZE = 14
NAME_HEIGHT = 18
NAME_GAP = 10

HEX_SIZE = 11
HEX_HEIGHT = 14
HEX_GAP = 2

GROUP_GAP = 24

PANEL_BG = {"dark": "#050505", "light": "#F3EFEC"}


def resolve_font(family: str) -> str | None:
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", family],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    path = result.stdout.strip()
    return path or None


def load_font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def scaled(value: float) -> float:
    return value * SCALE


def main() -> int:
    pal = palette.load()
    body = resolve_font("Google Sans")
    mono = resolve_font("Google Sans Code") or body
    header_font = load_font(body, int(scaled(HEADER_SIZE)))
    section_font = load_font(body, int(scaled(SECTION_SIZE)))
    name_font = load_font(body, int(scaled(NAME_SIZE)))
    hex_font = load_font(mono, int(scaled(HEX_SIZE)))

    groups = []
    for mode in ("dark", "light"):
        groups.append(
            [
                ("neutrals", list(pal["neutrals"][mode].items())),
                (
                    "chromatics",
                    [(name, pal["chroma"][mode][name]) for name in pal["chromatics"]],
                ),
                (
                    "bright chromatics",
                    [(name, pal["bright"][mode][name]) for name in pal["chromatics"]],
                ),
                ("derived tints", list(palette.tints(pal, mode)[0].items())),
            ]
        )

    group_height = (
        SECTION_HEIGHT
        + GROUP_TOP
        + CIRCLE_DIAMETER
        + NAME_GAP
        + NAME_HEIGHT
        + HEX_GAP
        + HEX_HEIGHT
    )
    panel_height = (
        PAD
        + HEADER_HEIGHT
        + HEADER_GAP
        + len(groups[0]) * group_height
        + (len(groups[0]) - 1) * GROUP_GAP
        + PAD
    )

    image = Image.new(
        "RGB", (int(scaled(WIDTH)), int(scaled(panel_height * 2))), (0, 0, 0)
    )
    draw = ImageDraw.Draw(image)

    for mode_index, mode in enumerate(("dark", "light")):
        panel_y = scaled(mode_index * panel_height)
        neutrals = pal["neutrals"][mode]
        draw.rectangle(
            [0, panel_y, scaled(WIDTH), panel_y + scaled(panel_height)],
            fill=rgb(PANEL_BG[mode]),
        )
        draw.text(
            (scaled(PAD), panel_y + scaled(PAD)),
            mode,
            anchor="lt",
            font=header_font,
            fill=rgb(neutrals["text"]),
        )

        y = panel_y + scaled(PAD + HEADER_HEIGHT + HEADER_GAP)
        for group_index, (label, swatches) in enumerate(groups[mode_index]):
            draw.text(
                (scaled(WIDTH) / 2, y),
                label,
                anchor="mt",
                font=section_font,
                fill=rgb(neutrals["muted"]),
            )
            y += scaled(SECTION_HEIGHT + GROUP_TOP)

            diameter = scaled(CIRCLE_DIAMETER)
            gap = scaled(CIRCLE_GAP)
            row_width = len(swatches) * diameter + (len(swatches) - 1) * gap
            x = (scaled(WIDTH) - row_width) / 2 + diameter / 2
            for name, hex_value in swatches:
                radius = diameter / 2
                draw.ellipse(
                    [x - radius, y, x + radius, y + diameter],
                    fill=rgb(hex_value),
                    outline=rgb(neutrals["line"]),
                    width=SCALE,
                )
                draw.text(
                    (x, y + diameter + scaled(NAME_GAP)),
                    name,
                    anchor="mt",
                    font=name_font,
                    fill=rgb(neutrals["text"]),
                )
                draw.text(
                    (x, y + diameter + scaled(NAME_GAP + NAME_HEIGHT + HEX_GAP)),
                    hex_value,
                    anchor="mt",
                    font=hex_font,
                    fill=rgb(neutrals["muted"]),
                )
                x += diameter + gap
            y += scaled(
                CIRCLE_DIAMETER + NAME_GAP + NAME_HEIGHT + HEX_GAP + HEX_HEIGHT
            )
            if group_index < len(groups[mode_index]) - 1:
                y += scaled(GROUP_GAP)

    image = image.resize(
        (WIDTH, panel_height * 2), Image.Resampling.LANCZOS
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "WEBP", quality=92, method=6)
    print(f"{image.width}x{image.height} -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
