#!/usr/bin/env python3
"""Derive the LUT palettes and the chezmoi data from meta/palette.toml, then verify them."""

from __future__ import annotations

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
CONTRAST_AA = 4.5
HUE_BASE_FLOOR = 4.5

HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})")
HEX_FULL_RE = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\b")
BARE_RE = re.compile(r"=\s*([0-9A-Fa-f]{6})\b")
RGBA_RE = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)")
BARE_EXEMPT: dict[str, set[str]] = {
    "home/dot_bashrc": {"HISTFILESIZE"},
}


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

LIGHT_LIGHTER = ("crust", "mantle")


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


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


def solve_gray(bg: str, ratio: float) -> str:
    y_bg = luminance(bg)
    y = (y_bg + 0.05) / ratio - 0.05
    if y <= 0:
        return "#000000"
    if y >= 1:
        return "#FFFFFF"
    c = 1.055 * y ** (1 / 2.4) - 0.055
    v = f"{round(min(max(c, 0.0), 1.0) * 255):02X}"
    return f"#{v}{v}{v}"


def solve_gray_lighter(bg: str, ratio: float) -> str:
    y = ratio * (luminance(bg) + 0.05) - 0.05
    y = min(max(y, 0.0), 1.0)
    c = 1.055 * y ** (1 / 2.4) - 0.055
    v = f"{round(min(max(c, 0.0), 1.0) * 255):02X}"
    return f"#{v}{v}{v}"


# The light ramp derives from the dark ramp by holding each role's contrast
# ratio to base; light base and text-max are the hand-set anchors in the
# source file. Only the dark ramp order defines role order downstream.
def load() -> dict:
    with SOURCE.open("rb") as fh:
        pal = tomllib.load(fh)
    dark = {role: hex_.upper() for role, hex_ in pal["neutrals"]["dark"].items()}
    light = {role: hex_.upper() for role, hex_ in pal["neutrals"]["light"].items()}
    for role, hex_ in dark.items():
        if role in light:
            continue
        ratio = contrast_ratio(hex_, dark["base"])
        light[role] = (
            solve_gray_lighter(light["base"], ratio)
            if role in LIGHT_LIGHTER
            else solve_gray(light["base"], ratio)
        )
    pal["neutrals"]["dark"] = dark
    pal["neutrals"]["light"] = {role: light[role] for role in dark}
    return pal


CHROMA_KEYS = {"dark": ("dark", "dark-bright"), "light": ("light", "light-bright")}


def chromatics(pal: dict, mode: str) -> dict[str, str]:
    base, _ = CHROMA_KEYS[mode]
    return {name: c[base].upper() for name, c in pal["chromatics"].items()}


def brights(pal: dict, mode: str) -> dict[str, str]:
    _, bright = CHROMA_KEYS[mode]
    return {name: c[bright].upper() for name, c in pal["chromatics"].items()}


def tint_hex(pal: dict, name: str, mode: str) -> str:
    tint = pal["tints"][name]
    if "anchor" in tint:
        La = rgb_to_oklch(hex_to_rgb(pal["neutrals"][mode][tint["anchor"]]))[0]
        Ch, Hh = rgb_to_oklch(hex_to_rgb(chromatics(pal, mode)[tint["hue"]]))[1:]
        return f"#{oklch_to_hex(La, Ch * float(tint['k']), Hh)}"
    value = tint[mode]
    return value.upper() if value.startswith("#") else value


def tint_hexes(pal: dict, mode: str) -> dict[str, str]:
    return {
        name: value
        for name in pal["tints"]
        if not (value := tint_hex(pal, name, mode)).startswith("rgba")
    }


def tint_overlays(pal: dict, mode: str) -> dict[str, str]:
    return {
        name: value
        for name in pal["tints"]
        if (value := tint_hex(pal, name, mode)).startswith("rgba")
    }


def build_lut(pal: dict, mode: str) -> str:
    neutrals = list(dict.fromkeys(pal["neutrals"][mode].values()))
    hues = list(
        dict.fromkeys(
            list(chromatics(pal, mode).values()) + list(brights(pal, mode).values())
        )
    )
    if len(neutrals) != 11 or len(hues) != 14:
        raise SystemExit(
            f"unexpected palette size ({mode}): {len(neutrals)} neutrals, "
            f"{len(hues)} chromatics"
        )

    ramp = sorted(neutrals, key=lambda h: rgb_to_oklch(hex_to_rgb(h))[0])
    base_lights = [rgb_to_oklch(hex_to_rgb(h))[0] for h in ramp]

    fillers: list[str] = []
    for a, b in zip(ramp, ramp[1:]):
        La, Ca, Ha = rgb_to_oklch(hex_to_rgb(a))
        Lb, Cb, Hb = rgb_to_oklch(hex_to_rgb(b))
        hold_h = Ha if Ca >= Cb else Hb
        for i in range(1, N_RAMP + 1):
            t = i / (N_RAMP + 1)
            fillers.append(
                oklch_to_hex(La + t * (Lb - La), Ca + t * (Cb - Ca), hold_h)
            )

    tints = list(fillers)
    for hex_ in hues:
        Lh, Ch, Hh = rgb_to_oklch(hex_to_rgb(hex_))
        for Lr in base_lights:
            chroma_value = Ch * max(0.0, 1 - abs(Lr - Lh) * K_CHROMA)
            if chroma_value > 1e-4:
                tints.append(oklch_to_hex(Lr, chroma_value, Hh))

    seen = set(neutrals) | set(hues)
    out = list(ramp) + hues
    for h in sorted(tints, key=lambda x: rgb_to_oklch(hex_to_rgb(x))[0]):
        if h not in seen:
            seen.add(h)
            out.append(h)
    return "\n".join(out) + "\n"


def normalize_rgba(value: str) -> str:
    m = RGBA_RE.fullmatch(value)
    if not m:
        return value
    r, g, b, a = m.groups()
    return f"rgba({r}, {g}, {b}, {a})"


def data_name(name: str) -> str:
    return name.replace("-", "_")


def data_entry(value: str) -> str:
    if value.startswith("rgba"):
        return f'{{ rgba: "{normalize_rgba(value)}" }}'
    return f'{{ hex: "{value}", bare: "{value[1:]}" }}'


def build_data(pal: dict, mode: str) -> str:
    neutrals = pal["neutrals"][mode]
    hues = chromatics(pal, mode)
    steps = brights(pal, mode)
    utility = {name: t["value"] for name, t in pal["utility"].items()}

    groups: list[tuple[str, list[tuple[str, str]]]] = [
        ("Neutrals, deepest ground role to maximal emphasis.", list(neutrals.items())),
        ("One Dark Pro hues, chroma ×1.5.", list(hues.items())),
        ("Bright step per hue.", [(f"{h}_bright", v) for h, v in steps.items()]),
        ("Derived and hand-written tints.", list(tint_hexes(pal, mode).items())),
        (
            "Alpha overlays and utility colors.",
            list(tint_overlays(pal, mode).items()) + list(utility.items()),
        ),
    ]
    names = [data_name(n) for _, group in groups for n, _ in group]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate data token name")
    lines = [
        "# Generated by meta/palette.py from meta/palette.toml; do not edit",
        "# by hand. Run make palette, then chezmoi apply.",
        "",
        f"mode: {mode}",
        "palette:",
    ]
    for comment, tokens in groups:
        lines.append(f"  # {comment}")
        for name, value in tokens:
            lines.append(f"  {data_name(name)}: {data_entry(value)}")
    return "\n".join(lines) + "\n"


def palette_hexes(pal: dict) -> set[str]:
    out: set[str] = set()
    for mode in MODES:
        out.update(pal["neutrals"][mode].values())
        out.update(chromatics(pal, mode).values())
        out.update(brights(pal, mode).values())
        out.update(tint_hexes(pal, mode).values())
    out.update(v for v in (t["value"] for t in pal["utility"].values()) if v.startswith("#"))
    return out


def allowed_hexes(pal: dict) -> set[str]:
    listed = {f"#{h.upper()}" for h in HEX_RE.findall(SOURCE.read_text())}
    return listed | palette_hexes(pal)


def drift_violations(pal: dict) -> dict[str, set[str]]:
    allowed = allowed_hexes(pal)
    violations: dict[str, set[str]] = {}
    for path in sorted((REPO / "home").rglob("*")):
        if not path.is_file() or "lutgen" in path.parts:
            continue
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


CONTRAST_GATES: list[tuple[str, str, float]] = [
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


def resolve_gate_color(pal: dict, mode: str, name: str) -> str:
    for source in (
        pal["neutrals"][mode],
        chromatics(pal, mode),
        brights(pal, mode),
    ):
        if name in source:
            return source[name]
    tints = tint_hexes(pal, mode)
    if name in tints:
        return tints[name]
    raise SystemExit(f"contrast gate references unknown role: {name!r}")


def gate_failures(pal: dict) -> list[str]:
    bad: list[str] = []
    for mode in MODES:
        for fg_name, bg_name, floor in CONTRAST_GATES:
            fg = resolve_gate_color(pal, mode, fg_name)
            bg = resolve_gate_color(pal, mode, bg_name)
            ratio = contrast_ratio(fg, bg)
            if ratio < floor:
                bad.append(
                    f"{mode}: {fg_name} on {bg_name} {ratio:.2f}:1 < {floor}:1"
                )
        for hue in chromatics(pal, mode):
            base_ratio = contrast_ratio(
                chromatics(pal, mode)[hue], pal["neutrals"][mode]["base"]
            )
            bright_ratio = contrast_ratio(
                brights(pal, mode)[hue], pal["neutrals"][mode]["base"]
            )
            if bright_ratio < base_ratio:
                bad.append(
                    f"{mode}: {hue} bright {bright_ratio:.2f}:1 does not emphasize "
                    f"over base {base_ratio:.2f}:1"
                )
            if base_ratio < HUE_BASE_FLOOR:
                bad.append(
                    f"{mode}: {hue} on base {base_ratio:.2f}:1 < {HUE_BASE_FLOOR}:1"
                )
    return bad


def contrast_report(pal: dict) -> list[str]:
    lines = []
    for mode in MODES:
        roles = pal["neutrals"][mode]
        hues = chromatics(pal, mode)
        tints = tint_hexes(pal, mode)
        base = roles.get("base")
        pairs = [
            ("text on base", roles.get("text"), base),
            ("subtext on base", roles.get("subtext"), base),
            ("muted on base", roles.get("muted"), base),
            ("text-max on base", roles.get("text-max"), base),
            ("accent on base", hues.get("blue"), base),
            ("text on selection", roles.get("text"), tints.get("selection")),
        ]
        lines.append(f"{mode}:")
        for label, fg, bg in pairs:
            if fg and bg:
                ratio = contrast_ratio(fg, bg)
                flag = f"  <-- below AA ({CONTRAST_AA})" if ratio < CONTRAST_AA else ""
                lines.append(f"  {label}: {ratio:.1f}:1{flag}")
    return lines


def read_mode() -> str:
    try:
        value = MODE_FILE.read_text().split()[0].lower()
    except (FileNotFoundError, IndexError):
        return "dark"
    if value not in MODES:
        raise SystemExit(
            f"{MODE_FILE}: unknown mode {value!r} (expected dark or light)"
        )
    return value


def resolve_mode(argv: list[str]) -> tuple[list[str], str]:
    args = [a for a in argv if not a.startswith("MODE=")]
    values = [a.split("=", 1)[1].lower() for a in argv if a.startswith("MODE=")]
    if values:
        if values[0] not in MODES:
            raise SystemExit(f"unknown mode {values[0]!r} (expected dark or light)")
        return args, values[0]
    return args, read_mode()


COMMANDS = {"all", "lut", "data", "check"}


def main(argv: list[str]) -> int:
    args, mode = resolve_mode(argv)
    command = args[0] if args else "all"
    if command not in COMMANDS or command == "--help":
        print(__doc__.strip())
        return 0 if command == "--help" else 2

    pal = load()

    if command in {"all", "lut"}:
        for m in MODES:
            text = build_lut(pal, m)
            path = LUTS[m]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            print(f"{text.count(chr(10))} colors -> {path}")

    if command in {"all", "data"}:
        text = build_data(pal, mode)
        DATA.write_text(text)
        print(f"{text.count(chr(10))} palette tokens -> {DATA} ({mode})")

    if command in {"all", "check"}:
        ok = True
        for m in MODES:
            path = LUTS[m]
            try:
                current = path.read_text()
            except FileNotFoundError:
                current = None
            if build_lut(pal, m) != current:
                print(f"check: {path.relative_to(REPO)} is stale; run make palette")
                ok = False
        try:
            current_data = DATA.read_text()
        except FileNotFoundError:
            current_data = None
        if build_data(pal, mode) != current_data:
            print(
                f"check: {DATA.relative_to(REPO)} is stale for mode {mode}; "
                "run make palette"
            )
            ok = False
        violations = drift_violations(pal)
        if violations:
            for f, hexes in sorted(violations.items()):
                print(f"{f}: {', '.join(sorted(hexes))}")
            ok = False
        else:
            print(f"check: every hex traces to the palette ({len(allowed_hexes(pal))} allowed)")
        gates = gate_failures(pal)
        if gates:
            for gate in gates:
                print(f"gate: {gate}")
            ok = False
        else:
            print(f"gates: all {len(CONTRAST_GATES)} contrast pairs pass in both modes")
        print("contrast (informational):")
        for line in contrast_report(pal):
            print(f"  {line}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
