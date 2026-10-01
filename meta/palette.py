#!/usr/bin/env python3
"""Derive tints, both LUT palettes, and the chezmoi data, then verify them."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "meta" / "color-scheme.md"
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


def solve_chroma(base_hex: str, target: float, bg: str) -> str:
    l0, c, h = rgb_to_oklch(hex_to_rgb(base_hex))
    y_target = (luminance(bg) + 0.05) / target - 0.05
    lo, hi = 0.0, l0
    for _ in range(50):
        mid = (lo + hi) / 2
        if luminance(oklch_to_hex(mid, c, h)) < y_target:
            lo = mid
        else:
            hi = mid
    return oklch_to_hex(hi, c, h)


# parse_rows reads meta/color-scheme.md as table data rather than prose.
# derive_tints rewrites the tint rows' hex columns in place. Never
# hand-reformat or reword those rows. Regenerate the doc with `make palette`.
def parse_rows(doc: str, start: str) -> list[tuple[str, list[str]]]:
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


def parse_neutrals(doc: str, mode: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_section = False
    in_mode = False
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.startswith("## Neutrals")
            continue
        if not in_section:
            continue
        if stripped.startswith("### "):
            in_mode = stripped[4:].strip().lower() == mode
            continue
        if stripped.startswith("|") and in_mode:
            cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].startswith("#") and len(cells[0]) == 7:
                out[cells[1]] = cells[0].upper()
    if mode == "light":
        dark = parse_neutrals(doc, "dark")
        base = out["base"]
        for role in ("crust", "mantle", "surface-0", "surface-1", "surface-2",
                     "line", "muted", "subtext", "text"):
            ratio = contrast_ratio(dark[role], dark["base"])
            if role in ("crust", "mantle"):
                out[role] = solve_gray_lighter(base, ratio)
            else:
                out[role] = solve_gray(base, ratio)
    return out


def parse_chromatics(doc: str, mode: str) -> dict[str, str]:
    column = 1 if mode == "dark" else 3
    return {
        cells[0]: cells[column].upper()
        for _, cells in parse_rows(doc, "## Chromatics")
        if len(cells) >= 5 and cells[column].startswith("#") and len(cells[column]) == 7
    }


def parse_brights(doc: str, mode: str) -> dict[str, str]:
    column = 2 if mode == "dark" else 4
    return {
        cells[0]: cells[column].upper()
        for _, cells in parse_rows(doc, "## Chromatics")
        if len(cells) >= 5 and cells[column].startswith("#") and len(cells[column]) == 7
    }


def parse_tint_specs(doc: str) -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    for _, cells in parse_rows(doc, "## Supporting tints"):
        if cells and all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if len(cells) == 7 and cells[0] != "Tint" and cells[1] != "n/a" and cells[2] != "n/a":
            out[cells[0]] = (cells[1], cells[2], cells[3])
    return out


def parse_tint_hexes(doc: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for _, cells in parse_rows(doc, "## Supporting tints"):
        if (
            len(cells) == 7
            and cells[0] != "Tint"
            and cells[4].startswith("#")
            and len(cells[4]) == 7
            and cells[5].startswith("#")
            and len(cells[5]) == 7
        ):
            out[cells[0]] = (cells[4].upper(), cells[5].upper())
    return out


def parse_tint_overlays(doc: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for _, cells in parse_rows(doc, "## Supporting tints"):
        if (
            len(cells) == 7
            and cells[0] != "Tint"
            and cells[4].startswith("rgba(")
            and cells[5].startswith("rgba(")
        ):
            out[cells[0]] = (cells[4], cells[5])
    return out


def parse_utility(doc: str) -> dict[str, str]:
    return {
        cells[0]: cells[1]
        for _, cells in parse_rows(doc, "## Utility colors")
        if len(cells) >= 3 and cells[1].startswith(("#", "rgba("))
    }


# doc_allowed collects hexes from "|" table lines only, because a hex
# that appears in prose is not part of the palette.
def doc_allowed(doc: str) -> set[str]:
    return {
        f"#{h.upper()}"
        for line in doc.splitlines()
        if line.lstrip().startswith("|")
        for h in HEX_RE.findall(line)
    }


def derive_tints(doc: str) -> str:
    neutrals = {m: parse_neutrals(doc, m) for m in MODES}
    chroma = {m: parse_chromatics(doc, m) for m in MODES}
    out: list[str] = []
    changed = 0
    in_section = False
    pending: list[tuple[str, list[str], str]] = []

    def widths() -> list[int]:
        w = [0] * 7
        for kind, cells, _ in pending:
            if kind == "sep":
                continue
            for i, c in enumerate(cells):
                w[i] = max(w[i], len(c))
        return w

    def flush() -> None:
        nonlocal changed
        if not pending:
            return
        w = widths()
        for kind, cells, raw in pending:
            if kind == "sep":
                dashes = " | ".join("-" * max(x, 3) for x in w)
                out.append(f"| {dashes} |\n")
                continue
            if kind == "spec":
                derived = cells[4:6]
                if any(h.strip("`") not in raw for h in derived):
                    changed += 1
            padded = " | ".join(c.ljust(x) for c, x in zip(cells, w))
            out.append(f"| {padded} |\n")
        pending.clear()

    def derive_row(cells: list[str]) -> list[str] | None:
        name, anchor, hue, k = cells[0], cells[1], cells[2], cells[3]
        try:
            kk = float(k)
        except ValueError:
            return None
        for m in MODES:
            if anchor not in neutrals[m] or hue not in chroma[m]:
                raise SystemExit(f"bad tint spec: {name} ({anchor!r}, {hue!r})")
        hexes = []
        for m in MODES:
            La = rgb_to_oklch(hex_to_rgb(neutrals[m][anchor]))[0]
            Ch, Hh = rgb_to_oklch(hex_to_rgb(chroma[m][hue]))[1:]
            hexes.append(f"`#{oklch_to_hex(La, Ch * kk, Hh)}`")
        return hexes

    for line in doc.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("## "):
            flush()
            in_section = stripped.startswith("## Supporting tints")
        elif in_section and stripped.startswith("|"):
            cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
            if len(cells) == 7 and all(re.fullmatch(r":?-+:?", c) for c in cells):
                pending.append(("sep", cells, line))
                continue
            if len(cells) == 7 and cells[0] != "Tint":
                derived = derive_row(cells)
                if derived is None:
                    raw = [c.strip() for c in stripped.strip("|").split("|")]
                    pending.append(("body", raw, line))
                else:
                    pending.append(("spec", cells[:4] + derived + cells[6:], line))
                continue
            pending.append(("head", cells, line))
            continue
        else:
            flush()
        out.append(line)
    flush()
    print(f"tints: {changed} derived hex values updated")
    return "".join(out)


def build_lut(doc: str, mode: str) -> str:
    neutrals = list(dict.fromkeys(parse_neutrals(doc, mode).values()))
    chromatics = list(
        dict.fromkeys(
            list(parse_chromatics(doc, mode).values())
            + list(parse_brights(doc, mode).values())
        )
    )
    if len(neutrals) != 11 or len(chromatics) != 14:
        raise SystemExit(
            f"unexpected palette size ({mode}): {len(neutrals)} neutrals, "
            f"{len(chromatics)} chromatics"
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
    for hex_ in chromatics:
        Lh, Ch, Hh = rgb_to_oklch(hex_to_rgb(hex_))
        for Lr in base_lights:
            chroma_value = Ch * max(0.0, 1 - abs(Lr - Lh) * K_CHROMA)
            if chroma_value > 1e-4:
                tints.append(oklch_to_hex(Lr, chroma_value, Hh))

    seen = set(neutrals) | set(chromatics)
    out = list(ramp) + chromatics
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


def build_data(doc: str, mode: str) -> str:
    neutrals = parse_neutrals(doc, mode)
    chroma = parse_chromatics(doc, mode)
    brights = parse_brights(doc, mode)
    tint_hexes = parse_tint_hexes(doc)
    overlays = parse_tint_overlays(doc)
    utility = parse_utility(doc)

    missing = [n for n in parse_tint_specs(doc) if n not in tint_hexes]
    if missing:
        raise SystemExit(
            f"tint rows missing generated hexes: {', '.join(missing)}; run make palette"
        )

    groups: list[tuple[str, list[tuple[str, str]]]] = [
        ("Neutrals, deepest ground role to maximal emphasis.", [(r, neutrals[r]) for r in neutrals]),
        ("One Dark Pro hues, chroma ×1.5.", [(h, chroma[h]) for h in chroma]),
        ("Bright step per hue.", [(f"{h}_bright", brights[h]) for h in brights]),
        (
            "Derived and hand-written tints.",
            [(n, tint_hexes[n][0] if mode == "dark" else tint_hexes[n][1]) for n in tint_hexes],
        ),
        (
            "Alpha overlays and utility colors.",
            [(n, overlays[n][0] if mode == "dark" else overlays[n][1]) for n in overlays]
            + [(n, utility[n]) for n in utility],
        ),
    ]
    names = [data_name(n) for _, group in groups for n, _ in group]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate data token name")
    lines = [
        "# Generated by meta/palette.py from meta/color-scheme.md; do not edit",
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


def drift_violations(doc: str) -> dict[str, set[str]]:
    allowed = doc_allowed(doc)
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

HUE_BASE_FLOOR = 4.5


def resolve_gate_color(doc: str, mode: str, name: str) -> str:
    for source in (
        parse_neutrals(doc, mode),
        parse_chromatics(doc, mode),
        parse_brights(doc, mode),
    ):
        if name in source:
            return source[name]
    tints = {
        n: (v[0] if mode == "dark" else v[1])
        for n, v in parse_tint_hexes(doc).items()
        if not (v[0] if mode == "dark" else v[1]).startswith("rgba")
    }
    if name in tints:
        return tints[name]
    raise SystemExit(f"contrast gate references unknown role: {name!r}")


def gate_failures(doc: str) -> list[str]:
    bad: list[str] = []
    for mode in MODES:
        for fg_name, bg_name, floor in CONTRAST_GATES:
            fg = resolve_gate_color(doc, mode, fg_name)
            bg = resolve_gate_color(doc, mode, bg_name)
            ratio = contrast_ratio(fg, bg)
            if ratio < floor:
                bad.append(
                    f"{mode}: {fg_name} on {bg_name} {ratio:.2f}:1 < {floor}:1"
                )
        for hue in parse_chromatics(doc, mode):
            base_ratio = contrast_ratio(
                parse_chromatics(doc, mode)[hue], parse_neutrals(doc, mode)["base"]
            )
            bright_ratio = contrast_ratio(
                parse_brights(doc, mode)[hue],
                parse_neutrals(doc, mode)["base"],
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


def contrast_report(doc: str) -> list[str]:
    tint_hexes = parse_tint_hexes(doc)
    lines = []
    for mode in MODES:
        roles = parse_neutrals(doc, mode)
        chroma = parse_chromatics(doc, mode)
        tints = {n: v[0] if mode == "dark" else v[1] for n, v in tint_hexes.items()}
        base = roles.get("base")
        pairs = [
            ("text on base", roles.get("text"), base),
            ("subtext on base", roles.get("subtext"), base),
            ("muted on base", roles.get("muted"), base),
            ("text-max on base", roles.get("text-max"), base),
            ("accent on base", chroma.get("blue"), base),
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


COMMANDS = {"all", "tints", "lut", "data", "check"}


def main(argv: list[str]) -> int:
    args, mode = resolve_mode(argv)
    command = args[0] if args else "all"
    if command not in COMMANDS or command == "--help":
        print(__doc__.strip())
        return 0 if command == "--help" else 2

    if command in {"all", "tints"}:
        doc = derive_tints(DOC.read_text())
        DOC.write_text(doc)
    else:
        doc = DOC.read_text()

    if command in {"all", "lut"}:
        for m in MODES:
            text = build_lut(doc, m)
            path = LUTS[m]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            print(f"{text.count(chr(10))} colors -> {path}")

    if command in {"all", "data"}:
        text = build_data(doc, mode)
        DATA.write_text(text)
        print(f"{text.count(chr(10))} palette tokens -> {DATA} ({mode})")

    if command in {"all", "check"}:
        doc = DOC.read_text()
        ok = True
        for m in MODES:
            path = LUTS[m]
            try:
                current = path.read_text()
            except FileNotFoundError:
                current = None
            if build_lut(doc, m) != current:
                print(f"check: {path.relative_to(REPO)} is stale; run make palette")
                ok = False
        try:
            current_data = DATA.read_text()
        except FileNotFoundError:
            current_data = None
        if build_data(doc, mode) != current_data:
            print(
                f"check: {DATA.relative_to(REPO)} is stale for mode {mode}; "
                "run make palette"
            )
            ok = False
        violations = drift_violations(doc)
        if violations:
            for f, hexes in sorted(violations.items()):
                print(f"{f}: {', '.join(sorted(hexes))}")
            ok = False
        else:
            print(f"check: every hex traces to the doc ({len(doc_allowed(doc))} allowed)")
        gates = gate_failures(doc)
        if gates:
            for gate in gates:
                print(f"gate: {gate}")
            ok = False
        else:
            print(f"gates: all {len(CONTRAST_GATES)} contrast pairs pass in both modes")
        print("contrast (informational):")
        for line in contrast_report(doc):
            print(f"  {line}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
