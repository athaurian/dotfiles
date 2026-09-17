#!/usr/bin/env python3
"""Palette machinery for the One Dark on Neutral scheme.

meta/color-scheme.md is the seed truth: the locked neutral ramp, the
One Dark Pro chromatics, and the tint specs. This script derives from
them and verifies the desktop stays in palette:

    palette.py            derive tints into the doc, write the LUT
                          palette, then run the checks (default)
    palette.py tints      rewrite the doc's tint Hex column only
    palette.py lut        write home/dot_config/lutgen/neutral only
    palette.py check      verify app-file hexes + report contrast

Everything is deterministic and idempotent: the same doc always
produces the same outputs. Stdlib only. See meta/lut-palette.md for
the LUT math and parameters.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "meta" / "color-scheme.md"
LUT = REPO / "home" / "dot_config" / "lutgen" / "neutral"

N_RAMP = 2  # intermediates between adjacent ramp steps
K_CHROMA = 0.5  # LUT tint chroma falloff toward the lightness extremes
CONTRAST_AA = 4.5

HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})")
HEX_FULL_RE = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\b")
BARE_RE = re.compile(r"=\s*([0-9A-Fa-f]{6})\b")  # foot-style key=value
BARE_EXEMPT: dict[str, set[str]] = {
    "home/dot_bashrc": {"HISTFILESIZE"},  # a number, not a color
}

# ---------------------------------------------------------------- color math

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
    # binary-search chroma down until the color fits sRGB
    lo, hi = 0.0, C
    for _ in range(20):
        mid = (lo + hi) / 2
        if in_gamut(L, mid, H):
            lo = mid
        else:
            hi = mid
    a, b = lo * math.cos(H), lo * math.sin(H)
    lms = tuple(x**3 for x in mat_mul(M2_INV, (L, a, b)))
    return rgb_to_hex(tuple(linear_to_srgb(c) for c in mat_mul(M1_INV, lms)))


def luminance(hex_: str) -> float:
    r, g, b = hex_to_rgb(hex_)
    lin = (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b))
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------- doc model

def parse_rows(doc: str, start: str) -> list[tuple[str, list[str]]]:
    """Table rows in the section whose header starts with `start`."""
    rows: list[tuple[str, list[str]]] = []
    in_section = False
    for line in doc.splitlines():
        if line.lstrip().startswith("## "):
            if in_section:
                break
            in_section = line.lstrip().startswith(start)
            continue
        if in_section and line.lstrip().startswith("|"):
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            rows.append((line, cells))
    return rows


def parse_neutrals(doc: str) -> dict[str, str]:
    return {
        cells[1]: cells[0].upper()
        for _, cells in parse_rows(doc, "## Neutrals")
        if len(cells) >= 2 and cells[0].startswith("#") and len(cells[0]) == 7
    }


def parse_chromatics(doc: str) -> dict[str, str]:
    return {
        cells[0]: cells[1].upper()
        for _, cells in parse_rows(doc, "## Chromatics")
        if len(cells) >= 3 and cells[1].startswith("#") and len(cells[1]) == 7
    }


def parse_tints(doc: str) -> dict[str, str]:
    """Derived spec rows only: tint name -> hex."""
    out: dict[str, str] = {}
    in_section = False
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.startswith("## Supporting tints")
            continue
        if not (in_section and stripped.startswith("|")):
            continue
        cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
        if (
            len(cells) == 6
            and cells[0] != "Tint"
            and cells[4].startswith("#")
            and len(cells[4]) == 7
        ):
            out[cells[0]] = cells[4].upper()
    return out


def section_hexes(doc: str, start: str, end: str) -> list[str]:
    section = doc[doc.index(start) : doc.index(end)]
    rows = [line for line in section.splitlines() if line.lstrip().startswith("|")]
    return [h.upper() for line in rows for h in HEX_RE.findall(line)]


def doc_allowed(doc: str) -> set[str]:
    """Every hex in a doc table (prose mentions are not part of the palette)."""
    return {
        f"#{h.upper()}"
        for line in doc.splitlines()
        if line.lstrip().startswith("|")
        for h in HEX_RE.findall(line)
    }


# ---------------------------------------------------------------- derivation

def derive_tints(doc: str) -> str:
    """Rewrites the Hex column of every spec row in the tints table."""
    neutrals = parse_neutrals(doc)
    chroma = parse_chromatics(doc)
    out: list[str] = []
    changed = 0
    in_section = False
    for line in doc.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.startswith("## Supporting tints")
        elif in_section and stripped.startswith("|"):
            cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
            if len(cells) == 6 and cells[0] != "Tint":
                name, anchor, hue, k, _, used = cells
                try:
                    khue = float(k)
                except ValueError:
                    out.append(line)  # alpha overlay: hand-written, not derived
                    continue
                if anchor not in neutrals or hue not in chroma:
                    raise SystemExit(f"bad tint spec: {name} ({anchor!r}, {hue!r})")
                La = rgb_to_oklch(hex_to_rgb(neutrals[anchor]))[0]
                Ch, Hh = rgb_to_oklch(hex_to_rgb(chroma[hue]))[1:]
                hex_ = oklch_to_hex(La, Ch * khue, Hh)
                if hex_ not in line:
                    changed += 1
                out.append(
                    f"| {name} | {anchor} | {hue} | {k} | `#{hex_}` | {used} |\n"
                )
                continue
        out.append(line)
    print(f"tints: {changed} derived hex(es) updated")
    return "".join(out)


def build_lut(doc: str) -> str:
    """The 115-color lutgen palette: locked hexes, then OKLCH
    intermediates, sorted by lightness."""
    neutrals = section_hexes(doc, "## Neutrals", "## Chromatics")
    chromatics = section_hexes(doc, "## Chromatics", "## Supporting tints")
    if len(neutrals) != 11 or len(chromatics) != 14:
        raise SystemExit(
            f"unexpected palette size: {len(neutrals)} neutrals, "
            f"{len(chromatics)} chromatics"
        )

    ramp = sorted(neutrals, key=lambda h: rgb_to_oklch(hex_to_rgb(h))[0])
    base_lights = [rgb_to_oklch(hex_to_rgb(h))[0] for h in ramp]

    fillers: list[str] = []
    for a, b in zip(ramp, ramp[1:]):
        La, Ca, Ha = rgb_to_oklch(hex_to_rgb(a))
        Lb, Cb, Hb = rgb_to_oklch(hex_to_rgb(b))
        # hue from the endpoint with the stronger chroma; near-greys
        # carry meaningless hue angles
        hold_h = Ha if Ca >= Cb else Hb
        for i in range(1, N_RAMP + 1):
            t = i / (N_RAMP + 1)
            fillers.append(
                oklch_to_hex(La + t * (Lb - La), Ca + t * (Cb - Ca), hold_h)
            )

    tints = list(fillers)
    for hex_ in chromatics[0::2]:
        Lh, Ch, Hh = rgb_to_oklch(hex_to_rgb(hex_))
        for Lr in base_lights:
            chroma = Ch * max(0.0, 1 - abs(Lr - Lh) * K_CHROMA)
            if chroma > 1e-4:
                tints.append(oklch_to_hex(Lr, chroma, Hh))

    seen = set(neutrals) | set(chromatics)
    out = list(ramp) + chromatics
    for h in sorted(tints, key=lambda x: rgb_to_oklch(hex_to_rgb(x))[0]):
        if h not in seen:
            seen.add(h)
            out.append(h)
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- checks

def drift_violations(doc: str) -> dict[str, set[str]]:
    """App-file hexes that do not trace to a doc table."""
    allowed = doc_allowed(doc)
    violations: dict[str, set[str]] = {}
    for path in sorted((REPO / "home").rglob("*")):
        if not path.is_file() or "lutgen" in path.parts:
            continue  # the LUT palette is the doc's output, not an app
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        rel = str(path.relative_to(REPO))
        exempt = BARE_EXEMPT.get(rel, set())
        found: set[str] = set()
        for m in HEX_FULL_RE.finditer(text):
            found.add(m.group(0)[:7].upper())
        for line in text.splitlines():
            if "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            if key.startswith("export "):
                key = key[len("export ") :].strip()
            if key in exempt:
                continue
            for m in BARE_RE.finditer(line):
                found.add(f"#{m.group(1).upper()}")
        for hex6 in found:
            if hex6 not in allowed:
                violations.setdefault(rel, set()).add(hex6)
    return violations


def contrast_report(doc: str) -> list[str]:
    """Informational WCAG ratios for the doc's documented role pairs."""
    roles = parse_neutrals(doc)
    chroma = parse_chromatics(doc)
    tints = parse_tints(doc)
    base = roles.get("base")
    pairs = [
        ("text on base", roles.get("text"), base),
        ("subtext on base", roles.get("subtext"), base),
        ("muted on base", roles.get("muted"), base),
        ("text-max on base", roles.get("text-max"), base),
        ("accent on base", chroma.get("blue"), base),
        ("text on selection", roles.get("text"), tints.get("selection")),
    ]
    lines = []
    for label, fg, bg in pairs:
        if fg and bg:
            ratio = contrast_ratio(fg, bg)
            flag = f"  <-- below AA ({CONTRAST_AA})" if ratio < CONTRAST_AA else ""
            lines.append(f"{label}: {ratio:.1f}:1{flag}")
    return lines


# ---------------------------------------------------------------- CLI

COMMANDS = {"all", "tints", "lut", "check"}


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "all"
    if command not in COMMANDS or argv[1:2] == ["--help"]:
        print(__doc__.strip())
        return 0 if argv[1:2] == ["--help"] else 2

    if command in {"all", "tints"}:
        doc = derive_tints(DOC.read_text())
        DOC.write_text(doc)
    else:
        doc = DOC.read_text()

    if command in {"all", "lut"}:
        text = build_lut(doc)
        LUT.parent.mkdir(parents=True, exist_ok=True)
        LUT.write_text(text)
        print(f"{text.count(chr(10))} colors -> {LUT}")

    if command in {"all", "check"}:
        doc = DOC.read_text()
        violations = drift_violations(doc)
        if violations:
            for f, hexes in sorted(violations.items()):
                print(f"{f}: {', '.join(sorted(hexes))}")
            ok = False
        else:
            print(f"check: every hex traces to the doc ({len(doc_allowed(doc))} allowed)")
            ok = True
        print("contrast (informational):")
        for line in contrast_report(doc):
            print(f"  {line}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
