#!/usr/bin/env python3
"""tree.py OUT SEED -- swaying-tree animation for the awww wallpaper daemon.

    python3 tree.py /tmp/anim-7.gif 7
    awww img --transition-type none /tmp/anim-7.gif && awww query

OUT may be "-" to write the GIF to stdout (`awww img - < ...` / pipe).

Design notes:
  * The loop is seamless: every oscillation is sin(k*t) with integer k and
    t = 2*pi*f/NFRAMES, so t=2*pi reproduces t=0 exactly.  The script renders
    one extra probe frame at f=NFRAMES and compares raw pixels with frame 0
    before saving; a mismatch is a bug, not a rounding artefact.
  * All randomness happens once, at tree-build time, from the seed.  Nothing
    in draw_frame() touches the RNG, or frames would not be reproducible.
  * Frames are quantized to PALETTE as they are produced (RGB frames at 1080p
    are ~6 MB each; keeping 100 of them around is not worth it).
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageSequence

TAU = 2.0 * math.pi

# ---------------------------------------------------------------- palette --
# Every hex here must be a locked entry in meta/color-scheme.md.  Quantizing
# each frame against this list makes it impossible to emit anything else.
C_SKY = "#202020"
C_HAZE = "#2D2D2D"
C_GROUND = "#3A3A3A"
C_BARK_DARK = "#5A5A5A"
C_BARK = "#8A8A8A"
C_BARK_LIT = "#B3B3B3"
C_LEAF_DARK = "#2B4218"
C_LEAF = "#89C952"
C_LEAF_LIT = "#B9EE7D"
C_BLOSSOM = "#FE4864"
C_FG = "#D4D4D4"

PALETTE_HEX = [
    C_SKY,
    C_HAZE,
    C_GROUND,
    C_BARK_DARK,
    C_BARK,
    C_BARK_LIT,
    C_LEAF_DARK,
    C_LEAF,
    C_LEAF_LIT,
    C_BLOSSOM,
    C_FG,
]


def rgb(h: str) -> Tuple[int, int, int]:
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


PALETTE = [rgb(h) for h in PALETTE_HEX]

# ------------------------------------------------------------ wind / sway --
SWAY_BASE = 0.010  # rad of sway for the trunk
SWAY_STEP = 0.0085  # extra rad per branching level (twigs move most)
SWAY_LAG = 0.42  # phase lag per level: the gust travels outwards
LEAF_FLUTTER = 0.16  # rad, harmonic 3
GRASS_SWAY = 0.30  # rad


def wind(t: float) -> float:
    """Gust shape in [-1, 1].  Harmonics 1 and 2 only -> period 2*pi."""
    return (math.sin(t) + 0.35 * math.sin(2.0 * t + 1.3)) / 1.35


# ----------------------------------------------------------------- config --
@dataclass
class Config:
    W: int
    H: int
    fps: int
    nframes: int
    ss: int  # supersample factor
    gain: float  # wind multiplier
    max_depth: int
    max_segs: int
    blossoms: bool
    unit: float = 1.0  # 1.0 at 1080p, everything scales off this
    horizon: float = 0.0
    root: Tuple[float, float] = (0.0, 0.0)


# ------------------------------------------------------------------- tree --
Leaf = Tuple[float, float, float, Tuple[int, int, int], float]  # r, a, size, col, phase


@dataclass
class Seg:
    parent: int
    angle: float  # rest angle relative to the parent's direction
    length: float
    width: float
    depth: int
    phase: float
    leaves: List[Leaf] = field(default_factory=list)


def _leaf_color(rng: random.Random, blossoms: bool) -> Tuple[int, int, int]:
    r = rng.random()
    if blossoms and r < 0.03:
        return rgb(C_BLOSSOM)
    if r < 0.35:
        return rgb(C_LEAF_DARK)
    if r < 0.85:
        return rgb(C_LEAF)
    return rgb(C_LEAF_LIT)


def _make_leaves(rng: random.Random, length: float, cfg: Config) -> List[Leaf]:
    out: List[Leaf] = []
    for _ in range(rng.randint(3, 5)):
        dist = rng.uniform(-0.45, 0.60) * length  # along the twig
        ang = rng.uniform(-0.95, 0.95)  # off its axis
        size = cfg.unit * rng.uniform(5.0, 9.5)
        out.append(
            (dist, ang, size, _leaf_color(rng, cfg.blossoms), rng.uniform(0, TAU))
        )
    return out


def build_tree(rng: random.Random, cfg: Config) -> List[Seg]:
    """Grow the skeleton once.  Parents always get a lower index than children,
    so a single forward pass can pose the whole tree."""
    segs: List[Seg] = []

    def grow(
        parent: int, rest_angle: float, length: float, width: float, depth: int
    ) -> None:
        if len(segs) >= cfg.max_segs:
            return
        idx = len(segs)
        segs.append(
            Seg(parent, rest_angle, length, max(1.0, width), depth, rng.uniform(0, TAU))
        )

        tip = (
            depth >= cfg.max_depth
            or length < cfg.unit * 12.0
            or (depth >= 4 and rng.random() < 0.08)
        )
        if tip:
            segs[idx].leaves = _make_leaves(rng, length, cfg)
            return

        r = rng.random()
        n = 3 if (depth <= 2 and r < 0.35) else (1 if r > 0.93 else 2)
        spread = rng.uniform(0.34, 0.62)
        for i in range(n):
            if n == 1:
                a = rng.uniform(-0.18, 0.18)
            else:
                a = (i / (n - 1) - 0.5) * 2.0 * spread + rng.uniform(-0.12, 0.12)
            grow(
                idx,
                a,
                length * rng.uniform(0.74, 0.86),
                width * rng.uniform(0.62, 0.72),
                depth + 1,
            )

    grow(-1, rng.uniform(-0.05, 0.05), cfg.unit * 165.0, cfg.unit * 26.0, 0)
    return segs


def pose(segs: List[Seg], t: float, cfg: Config):
    """Absolute geometry of every segment at time t."""
    n = len(segs)
    bx = [0.0] * n
    by = [0.0] * n
    tx = [0.0] * n
    ty = [0.0] * n
    aa = [0.0] * n
    rx, ry = cfg.root
    for i, s in enumerate(segs):
        if s.parent < 0:
            x0, y0, pa = rx, ry, 0.0
        else:
            p = s.parent
            x0, y0, pa = tx[p], ty[p], aa[p]
        amp = cfg.gain * (SWAY_BASE + SWAY_STEP * s.depth)
        a = pa + s.angle + amp * wind(t - SWAY_LAG * s.depth + 0.7 * s.phase)
        bx[i], by[i], aa[i] = x0, y0, a
        tx[i] = x0 + s.length * math.sin(a)
        ty[i] = y0 - s.length * math.cos(a)
    return bx, by, tx, ty, aa


def bark_color(depth: int) -> Tuple[int, int, int]:
    if depth <= 1:
        return rgb(C_BARK_LIT)
    if depth <= 3:
        return rgb(C_BARK)
    return rgb(C_BARK_DARK)


# ------------------------------------------------------------- background --
def make_background(cfg: Config) -> Image.Image:
    S = cfg.ss
    img = Image.new("RGB", (cfg.W * S, cfg.H * S), rgb(C_SKY))
    d = ImageDraw.Draw(img)
    hz = cfg.horizon
    # distant haze / hills, then the ground slab
    d.ellipse(
        [
            -0.15 * cfg.W * S,
            (hz - 120 * cfg.unit) * S,
            0.55 * cfg.W * S,
            (hz + 200 * cfg.unit) * S,
        ],
        fill=rgb(C_HAZE),
    )
    d.ellipse(
        [
            0.45 * cfg.W * S,
            (hz - 70 * cfg.unit) * S,
            1.25 * cfg.W * S,
            (hz + 200 * cfg.unit) * S,
        ],
        fill=rgb(C_HAZE),
    )
    d.rectangle([0, hz * S, cfg.W * S, cfg.H * S], fill=rgb(C_GROUND))
    return img


def make_grass(rng: random.Random, cfg: Config):
    blades = []
    for _ in range(90):
        x = rng.uniform(-0.02, 1.02) * cfg.W
        h = cfg.unit * rng.uniform(10.0, 28.0)
        blades.append(
            (
                x,
                h,
                rng.uniform(0, TAU),
                rgb(C_LEAF_DARK) if rng.random() < 0.7 else rgb(C_BARK_DARK),
            )
        )
    return blades


def make_fallers(rng: random.Random, cfg: Config):
    """Drifting leaves.  p(t) wraps once (or twice) per loop, and the entry /
    exit points are off-screen, so the wrap is never visible."""
    out = []
    for _ in range(9):
        out.append(
            (
                rng.uniform(0.05, 0.95) * cfg.W,  # x anchor
                rng.random(),  # phase along fall
                1 if rng.random() < 0.75 else 2,  # laps per loop
                rng.choice([1, 2]),  # sway harmonic
                rng.uniform(0, TAU),  # sway phase
                cfg.unit * rng.uniform(4.0, 7.0),  # size
                _leaf_color(rng, cfg.blossoms),
            )
        )
    return out


# ------------------------------------------------------------------ frame --
def draw_frame(img: Image.Image, segs, grass, fallers, t: float, cfg: Config) -> None:
    S = cfg.ss
    d = ImageDraw.Draw(img)
    hz = cfg.horizon

    # grass, behind the tree
    gw = max(1, int(round(2.0 * cfg.unit * S)))
    for x, h, ph, col in grass:
        a = GRASS_SWAY * wind(t + ph)
        d.line(
            [x * S, hz * S, (x + h * math.sin(a)) * S, (hz - h * math.cos(a)) * S],
            fill=col,
            width=gw,
        )

    bx, by, tx, ty, aa = pose(segs, t, cfg)

    # branches
    for i, s in enumerate(segs):
        w = max(1, int(round(s.width * S)))
        col = bark_color(s.depth)
        d.line([bx[i] * S, by[i] * S, tx[i] * S, ty[i] * S], fill=col, width=w)
        if w >= 4:  # round off the joint
            r = w / 2.0
            d.ellipse(
                [tx[i] * S - r, ty[i] * S - r, tx[i] * S + r, ty[i] * S + r], fill=col
            )

    # leaves on top
    for i, s in enumerate(segs):
        for dist, la, size, col, ph in s.leaves:
            a = aa[i] + la + LEAF_FLUTTER * math.sin(3.0 * t + ph)
            x = tx[i] + dist * math.sin(a)
            y = ty[i] - dist * math.cos(a)
            d.ellipse(
                [
                    (x - size) * S,
                    (y - size * 0.8) * S,
                    (x + size) * S,
                    (y + size * 0.8) * S,
                ],
                fill=col,
            )

    # falling leaves
    top, bottom = -0.08 * cfg.H, 1.10 * cfg.H
    for x0, p0, laps, k, ph, size, col in fallers:
        p = (p0 + laps * t / TAU) % 1.0
        y = top + p * (bottom - top)
        x = x0 + 28.0 * cfg.unit * math.sin(TAU * k * p + ph)
        d.ellipse(
            [
                (x - size) * S,
                (y - size * 0.8) * S,
                (x + size) * S,
                (y + size * 0.8) * S,
            ],
            fill=col,
        )


def quantize(img: Image.Image, pal_img: Image.Image) -> Image.Image:
    return img.quantize(palette=pal_img, dither=Image.Dither.NONE)


# ------------------------------------------------------------------- main --
def report(path: str) -> None:
    im = Image.open(path)
    n, total = 0, 0
    for fr in ImageSequence.Iterator(im):
        n += 1
        total += fr.info.get("duration", 0)
    first = Image.open(path).convert("RGB")
    colors = first.getcolors(4096) or []
    print(
        f"  saved     {path} ({os.path.getsize(path) / 1024:.0f} KB)", file=sys.stderr
    )
    print(
        f"  stored    {n} frames (Pillow merges identical ones), "
        f"{total / 1000:.2f} s playing time",
        file=sys.stderr,
    )
    print(
        f"  frame 0   {len(colors)} distinct colors (palette has {len(PALETTE)})",
        file=sys.stderr,
    )


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Swaying-tree GIF for awww.")
    ap.add_argument("out", help='output .gif, or "-" for stdout')
    ap.add_argument("seed", type=int)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--seconds", type=float, default=8.0, help="loop length")
    ap.add_argument(
        "--ss", type=int, default=2, help="supersample factor (1 = hard pixels)"
    )
    ap.add_argument("--wind", type=float, default=1.0, help="sway gain")
    ap.add_argument("--depth", type=int, default=7)
    ap.add_argument("--max-segs", type=int, default=1600)
    ap.add_argument("--no-blossoms", action="store_true")
    ap.add_argument("--no-check", action="store_true", help="skip the seam probe")
    args = ap.parse_args(argv)

    nframes = max(2, int(round(args.fps * args.seconds)))
    cfg = Config(
        W=args.width,
        H=args.height,
        fps=args.fps,
        nframes=nframes,
        ss=max(1, args.ss),
        gain=args.wind,
        max_depth=args.depth,
        max_segs=args.max_segs,
        blossoms=not args.no_blossoms,
    )
    cfg.unit = cfg.H / 1080.0
    cfg.horizon = cfg.H * 0.88

    t0 = time.time()
    rng = random.Random(args.seed)
    cfg.root = (cfg.W * (0.5 + rng.uniform(-0.06, 0.06)), cfg.horizon + 6.0 * cfg.unit)

    segs = build_tree(rng, cfg)
    grass = make_grass(rng, cfg)
    fallers = make_fallers(rng, cfg)
    nleaves = sum(len(s.leaves) for s in segs)

    pal_img = Image.new("P", (1, 1))
    # Pad by repeating the palette, not with zeros: Pillow treats every one
    # of the 256 slots as a quantization candidate, so zero-padding adds a
    # stray black that LANCZOS-blended edge pixels can snap to (ss > 1).
    flat = [c for col in PALETTE for c in col]
    pal_img.putpalette((flat * ((768 // len(flat)) + 1))[:768])

    bg = make_background(cfg)
    frames: List[Image.Image] = []
    first_bytes = b""
    probe_bytes = b""

    # nframes + 1: the last one is the seam probe (t = 2*pi), never saved.
    for f in range(nframes + (0 if args.no_check else 1)):
        t = TAU * f / nframes
        img = bg.copy()
        draw_frame(img, segs, grass, fallers, t, cfg)
        if cfg.ss > 1:
            img = img.resize((cfg.W, cfg.H), Image.LANCZOS)
        if f == nframes:
            probe_bytes = img.tobytes()
            break
        if f == 0:
            first_bytes = img.tobytes()
        frames.append(quantize(img, pal_img))

    if not args.no_check:
        if probe_bytes != first_bytes:
            print(
                "ERROR: frame[nframes] != frame[0] -- loop is not seamless "
                "(an oscillation does not complete whole periods)",
                file=sys.stderr,
            )
            return 2
        print("  seam      frame[N] == frame[0], pixel-identical", file=sys.stderr)

    duration = int(round(1000.0 / cfg.fps))
    if args.out == "-":
        frames[0].save(
            sys.stdout.buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
        )
        sys.stdout.buffer.flush()
    else:
        frames[0].save(
            args.out, save_all=True, append_images=frames[1:], duration=duration, loop=0
        )

    print(
        f"  tree      seed {args.seed}: {len(segs)} segments, {nleaves} leaves, "
        f"depth {cfg.max_depth}",
        file=sys.stderr,
    )
    print(
        f"  rendered  {nframes} frames @ {cfg.W}x{cfg.H}, {cfg.fps} fps "
        f"(ss={cfg.ss}) in {time.time() - t0:.1f} s",
        file=sys.stderr,
    )
    if args.out != "-":
        report(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
