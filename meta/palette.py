#!/usr/bin/env python3
"""Derives the LUT palettes and the chezmoi data from meta/palette.toml, then verifies them."""

import math
import re
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "meta" / "palette.toml"
LUTS = {
    "dark": REPO / "home" / "dot_config" / "lutgen" / "neutral",
    "light": REPO / "home" / "dot_config" / "lutgen" / "neutral-light",
}
DATA = REPO / "home" / ".chezmoidata.yaml"
MODE_FILE = Path("~/.local/state/palette-mode").expanduser()
MODES = ("dark", "light")

N_RAMP = 2
K_CHROMA = 0.5
HUE_BASE_FLOOR = 4.5
LIGHT_LIGHTER = ("crust", "mantle")

HEX_FULL_RE = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\b")
BARE_RE = re.compile(r"=\s*([0-9A-Fa-f]{6})\b")
BARE_EXEMPT = {"home/dot_bashrc": {"HISTFILESIZE"}}

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


def mat_mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "".join(f"{round(min(max(c, 0.0), 1.0) * 255):02X}" for c in rgb)


def rgb_to_oklch(rgb):
    lin = tuple(srgb_to_linear(c) for c in rgb)
    lms = tuple(x ** (1 / 3) for x in mat_mul(M1, lin))
    L, a, b = mat_mul(M2, lms)
    return L, math.hypot(a, b), math.atan2(b, a)


def oklch_srgb(L, C, H):
    a, b = C * math.cos(H), C * math.sin(H)
    lms = tuple(x**3 for x in mat_mul(M2_INV, (L, a, b)))
    return [linear_to_srgb(c) for c in mat_mul(M1_INV, lms)]


def oklch_to_hex(L, C, H):
    lo, hi = 0.0, C
    for _ in range(20):
        mid = (lo + hi) / 2
        if all(-1e-6 <= c <= 1 + 1e-6 for c in oklch_srgb(L, mid, H)):
            lo = mid
        else:
            hi = mid
    return rgb_to_hex(oklch_srgb(L, lo, H))


def luminance(h):
    r, g, b = (srgb_to_linear(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def gray(y):
    if y <= 0:
        return "#000000"
    if y >= 1:
        return "#FFFFFF"
    c = 1.055 * y ** (1 / 2.4) - 0.055
    v = f"{round(min(max(c, 0.0), 1.0) * 255):02X}"
    return f"#{v}{v}{v}"


def solve_gray(bg, ratio):
    return gray((luminance(bg) + 0.05) / ratio - 0.05)


def solve_gray_lighter(bg, ratio):
    return gray(ratio * (luminance(bg) + 0.05) - 0.05)


# The light table holds only base and text-max. The other roles derive from
# the dark ramp, each keeping its contrast ratio to base, so the two ramps
# stay in step.
def load():
    with SOURCE.open("rb") as fh:
        pal = tomllib.load(fh)
    dark = {r: h.upper() for r, h in pal["neutrals"]["dark"].items()}
    light = {r: h.upper() for r, h in pal["neutrals"]["light"].items()}
    for role, hex_ in dark.items():
        if role not in light:
            ratio = contrast(hex_, dark["base"])
            light[role] = (
                solve_gray_lighter(light["base"], ratio)
                if role in LIGHT_LIGHTER
                else solve_gray(light["base"], ratio)
            )
    pal["neutrals"] = {"dark": dark, "light": {r: light[r] for r in dark}}
    pal["chroma"], pal["bright"] = {}, {}
    for mode, base_key, bright_key in (
        ("dark", "dark", "dark-bright"),
        ("light", "light", "light-bright"),
    ):
        pal["chroma"][mode] = {n: c[base_key].upper() for n, c in pal["chromatics"].items()}
        pal["bright"][mode] = {n: c[bright_key].upper() for n, c in pal["chromatics"].items()}
    return pal


def tint(pal, name, mode):
    spec = pal["tints"][name]
    if "anchor" in spec:
        La = rgb_to_oklch(hex_to_rgb(pal["neutrals"][mode][spec["anchor"]]))[0]
        Ch, Hh = rgb_to_oklch(hex_to_rgb(pal["chroma"][mode][spec["hue"]]))[1:]
        return f"#{oklch_to_hex(La, Ch * float(spec['k']), Hh)}"
    value = spec[mode]
    return value.upper() if value.startswith("#") else value


def tints(pal, mode):
    hexes, overlays = {}, {}
    for name in pal["tints"]:
        value = tint(pal, name, mode)
        (overlays if value.startswith("rgba") else hexes)[name] = value
    return hexes, overlays


def build_lut(pal, mode):
    neutrals = list(dict.fromkeys(pal["neutrals"][mode].values()))
    hues = list(
        dict.fromkeys([*pal["chroma"][mode].values(), *pal["bright"][mode].values()])
    )
    if len(neutrals) != 11 or len(hues) != 14:
        raise SystemExit(
            f"unexpected palette size ({mode}): {len(neutrals)} neutrals, "
            f"{len(hues)} chromatics"
        )

    ramp = sorted(neutrals, key=lambda h: rgb_to_oklch(hex_to_rgb(h))[0])
    lights = [rgb_to_oklch(hex_to_rgb(h))[0] for h in ramp]

    mixes = []
    for a, b in zip(ramp, ramp[1:]):
        La, Ca, Ha = rgb_to_oklch(hex_to_rgb(a))
        Lb, Cb, Hb = rgb_to_oklch(hex_to_rgb(b))
        hold_h = Ha if Ca >= Cb else Hb
        for i in range(1, N_RAMP + 1):
            t = i / (N_RAMP + 1)
            mixes.append(oklch_to_hex(La + t * (Lb - La), Ca + t * (Cb - Ca), hold_h))

    for hex_ in hues:
        Lh, Ch, Hh = rgb_to_oklch(hex_to_rgb(hex_))
        for Lr in lights:
            c = Ch * max(0.0, 1 - abs(Lr - Lh) * K_CHROMA)
            if c > 1e-4:
                mixes.append(oklch_to_hex(Lr, c, Hh))

    seen = set(neutrals) | set(hues)
    out = ramp + hues
    for h in sorted(mixes, key=lambda x: rgb_to_oklch(hex_to_rgb(x))[0]):
        if h not in seen:
            seen.add(h)
            out.append(h)
    return "\n".join(out) + "\n"


def build_data(pal, mode):
    hex_tints, overlays = tints(pal, mode)
    utility = {n: t["value"] for n, t in pal["utility"].items()}
    groups = [
        ("Neutrals, deepest ground role to maximal emphasis.", pal["neutrals"][mode].items()),
        ("One Dark Pro hues, chroma ×1.5.", pal["chroma"][mode].items()),
        ("Bright step per hue.", [(f"{h}_bright", v) for h, v in pal["bright"][mode].items()]),
        ("Derived and hand-written tints.", hex_tints.items()),
        ("Alpha overlays and utility colors.", [*overlays.items(), *utility.items()]),
    ]
    names = [n.replace("-", "_") for _, group in groups for n, _ in group]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate data token name")
    lines = [
        "# Generated by meta/palette.py from meta/palette.toml.",
        "# Do not edit by hand. Run make palette, then chezmoi apply.",
        "",
        f"mode: {mode}",
        "palette:",
    ]
    for comment, tokens in groups:
        lines.append(f"  # {comment}")
        for name, value in tokens:
            lines.append(f"  {name.replace('-', '_')}: {data_entry(value)}")
    return "\n".join(lines) + "\n"


def data_entry(value):
    if value.startswith("rgba"):
        return f'{{ rgba: "{value}" }}'
    return f'{{ hex: "{value}", bare: "{value[1:]}" }}'


def palette_values(pal):
    out = set()
    for mode in MODES:
        out.update(pal["neutrals"][mode].values())
        out.update(pal["chroma"][mode].values())
        out.update(pal["bright"][mode].values())
        out.update(tints(pal, mode)[0].values())
    out.update(t["value"] for t in pal["utility"].values() if t["value"].startswith("#"))
    return out


def drift(allowed):
    violations = {}
    for path in sorted((REPO / "home").rglob("*")):
        if not path.is_file() or "lutgen" in path.parts:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        rel = str(path.relative_to(REPO))
        exempt = BARE_EXEMPT.get(rel, set())
        found = {m.group(0)[:7].upper() for m in HEX_FULL_RE.finditer(text)}
        for line in text.splitlines():
            if "=" not in line:
                continue
            key = line.split("=", 1)[0].strip().removeprefix("export ").strip()
            if key not in exempt:
                found.update(f"#{m.group(1).upper()}" for m in BARE_RE.finditer(line))
        bad = found - allowed
        if bad:
            violations[rel] = bad
    return violations


CONTRAST_GATES = [
    ("text", "base", 10.0),
    ("subtext", "base", 7.0),
    ("muted", "base", 4.5),
    ("text", "surface-0", 4.5),
    ("text", "surface-1", 4.5),
    ("text", "surface-2", 4.5),
    ("subtext", "surface-1", 4.0),
    ("muted", "surface-1", 3.5),
    ("line", "base", 1.5),
    ("line", "surface-2", 1.2),
    ("on-accent", "blue", 4.5),
    ("text", "selection-deep", 4.5),
    ("blue", "notice", 4.0),
    ("yellow", "warning-hover", 4.0),
    ("red", "error-hover", 4.0),
    ("red", "urgent", 4.0),
]


def gate_failures(pal):
    bad = []
    for mode in MODES:
        neutrals, chroma = pal["neutrals"][mode], pal["chroma"][mode]
        bright, hex_tints = pal["bright"][mode], tints(pal, mode)[0]

        def color(name):
            for source in (neutrals, chroma, bright, hex_tints):
                if name in source:
                    return source[name]
            raise SystemExit(f"contrast gate references unknown role: {name!r}")

        for fg, bg, floor in CONTRAST_GATES:
            ratio = contrast(color(fg), color(bg))
            if ratio < floor:
                bad.append(f"{mode}: {fg} on {bg} {ratio:.2f}:1 < {floor}:1")
        for hue in chroma:
            base = contrast(chroma[hue], neutrals["base"])
            step = contrast(bright[hue], neutrals["base"])
            if step < base:
                bad.append(
                    f"{mode}: {hue} bright {step:.2f}:1 does not emphasize "
                    f"over base {base:.2f}:1"
                )
            if base < HUE_BASE_FLOOR:
                bad.append(f"{mode}: {hue} on base {base:.2f}:1 < {HUE_BASE_FLOOR}:1")
    return bad


def active_mode(argv):
    for arg in argv:
        if arg.startswith("MODE="):
            mode = arg.split("=", 1)[1].lower()
            if mode not in MODES:
                raise SystemExit(f"unknown mode {mode!r} (expected dark or light)")
            return mode
    extra = [a for a in argv if not a.startswith("MODE=")]
    if extra:
        raise SystemExit(f"unexpected argument: {extra[0]}")
    try:
        mode = MODE_FILE.read_text().split()[0].lower()
    except (FileNotFoundError, IndexError):
        return "dark"
    if mode not in MODES:
        raise SystemExit(f"{MODE_FILE}: unknown mode {mode!r} (expected dark or light)")
    return mode


def main(argv):
    mode = active_mode(argv)
    pal = load()
    for lut_mode, path in LUTS.items():
        text = build_lut(pal, lut_mode)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"{text.count(chr(10))} colors -> {path}")
    text = build_data(pal, mode)
    DATA.write_text(text)
    print(f"{text.count(chr(10))} palette tokens -> {DATA} ({mode})")

    values = palette_values(pal)
    violations = drift(values)
    failures = gate_failures(pal)
    for rel, hexes in sorted(violations.items()):
        print(f"{rel}: {', '.join(sorted(hexes))}")
    for line in failures:
        print(f"gate: {line}")
    if violations or failures:
        return 1
    print(f"check: every hex is a palette value ({len(values)} allowed)")
    print(f"gates: all {len(CONTRAST_GATES)} contrast pairs pass in both modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
