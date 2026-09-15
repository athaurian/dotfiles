#!/usr/bin/env python3
"""Generates the lutgen palette from the locked colors in
meta/color-scheme.md: locked hexes first, then OKLCH-interpolated
intermediates, sorted by lightness. One-shot; re-run after editing the
color scheme doc. See meta/lut-palette.md for the math and parameters.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "meta" / "color-scheme.md"
OUT = REPO / "home" / "dot_config" / "lutgen" / "neutral"

N_RAMP = 2
K_CHROMA = 0.5

HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})")

M1 = (
    (0.4122214708, 0.5363325363, 0.0514459929),
    (0.2119034982, 0.6806995451, 0.1073969566),
    (0.0883024619, 0.2817188376, 0.6299787005),
)
M2 = (
    (0.2104542553, 0.7936177850, -0.0040720468),
    (1.9779984951, -2.4285922050, 0.4505937099),
    (0.0259040371, 0.7827717662, -0.8086757660),
)
M2_INV = (
    (1.0, 0.3963377774, 0.2158037573),
    (1.0, -0.1055613458, -0.0638541728),
    (1.0, -0.0894841775, -1.2914855480),
)
M1_INV = (
    (4.0767416621, -3.3077115913, 0.2309699292),
    (-1.2684380046, 2.6097574011, -0.3413193965),
    (-0.0041960863, -0.7034186147, 1.7076147010),
)


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "".join(
        f"{round(min(max(c, 0.0), 1.0) * 255):02X}" for c in rgb
    )


def mat_mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def rgb_to_oklch(rgb):
    lin = tuple(srgb_to_linear(c) for c in rgb)
    lms = tuple(x ** (1 / 3) for x in mat_mul(M1, lin))
    L, a, b = mat_mul(M2, lms)
    return L, math.hypot(a, b), math.atan2(b, a)


def in_gamut(L: float, C: float, H: float) -> bool:
    a, b = C * math.cos(H), C * math.sin(H)
    lms = tuple(x**3 for x in mat_mul(M2_INV, (L, a, b)))
    rgb = tuple(linear_to_srgb(c) for c in mat_mul(M1_INV, lms))
    return all(-1e-6 <= c <= 1 + 1e-6 for c in rgb)


def oklch_to_hex(L: float, C: float, H: float) -> str:
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        if in_gamut(L, mid, H):
            lo = mid
        else:
            hi = mid
    a, b = lo * math.cos(H), lo * math.sin(H)
    lms = tuple(x**3 for x in mat_mul(M2_INV, (L, a, b)))
    return rgb_to_hex(tuple(linear_to_srgb(c) for c in mat_mul(M1_INV, lms)))


def table_hexes(doc: str, start: str, end: str) -> list[str]:
    section = doc[doc.index(start) : doc.index(end)]
    rows = [line for line in section.splitlines() if line.lstrip().startswith("|")]
    return [h.upper() for line in rows for h in HEX_RE.findall(line)]


def main() -> None:
    doc = DOC.read_text()
    neutrals = table_hexes(doc, "## Neutrals", "## Chromatics")
    chromatics = table_hexes(doc, "## Chromatics", "## Supporting tints")
    if len(neutrals) != 11 or len(chromatics) != 14:
        raise SystemExit(
            f"unexpected palette size: {len(neutrals)} neutrals, "
            f"{len(chromatics)} chromatics"
        )

    ramp = sorted(neutrals, key=lambda h: rgb_to_oklch(hex_to_rgb(h))[0])
    base_lights = [rgb_to_oklch(hex_to_rgb(h))[0] for h in ramp]

    locked: list[str] = []
    for a, b in zip(ramp, ramp[1:]):
        La, Ca, Ha = rgb_to_oklch(hex_to_rgb(a))
        Lb, Cb, Hb = rgb_to_oklch(hex_to_rgb(b))
        # hue from the endpoint with the stronger chroma; near-greys
        # carry meaningless hue angles
        hold_h = Ha if Ca >= Cb else Hb
        for i in range(1, N_RAMP + 1):
            t = i / (N_RAMP + 1)
            locked.append(
                oklch_to_hex(La + t * (Lb - La), Ca + t * (Cb - Ca), hold_h)
            )
    generated = list(locked)
    for hex_ in chromatics[0::2]:
        Lh, Ch, Hh = rgb_to_oklch(hex_to_rgb(hex_))
        for Lr in base_lights:
            chroma = Ch * max(0.0, 1 - abs(Lr - Lh) * K_CHROMA)
            if chroma > 1e-4:
                generated.append(oklch_to_hex(Lr, chroma, Hh))

    seen = set(neutrals) | set(chromatics)
    out = list(ramp) + chromatics
    for h in sorted(generated, key=lambda x: rgb_to_oklch(hex_to_rgb(x))[0]):
        if h not in seen:
            seen.add(h)
            out.append(h)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out) + "\n")
    print(f"{len(out)} colors -> {OUT}")


if __name__ == "__main__":
    main()
