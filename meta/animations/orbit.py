#!/usr/bin/env python3
"""orbit.py OUT SEED -- binary orbit around lowercase thinkpad.  For awww.

    python3 orbit.py /tmp/orbit-2.gif 2
    awww img --transition-type none /tmp/orbit-2.gif && awww query

OUT may be "-" to write the GIF to stdout (`awww img - < ...` / pipe).

Design notes:
  * Restraint is the whole piece: an empty base ground, nine fixed faint
    stars, a hairline ring with a white and a grey dot in binary orbit,
    and lowercase thinkpad over a `word...` status line with a small
    loading spinner (dark ring + circling white arc) beside it.  Every
    word in spinner_words.txt cycles through the loop exactly once, in a
    per-seed shuffled order, each on screen for --word-seconds
    (default 3 s); the total loop grows to fit them (~9 min default).
    Each frame's spinner+word row is centered on the screen, so
    short words sit centered rather than left-weighted. The subtext
    carries a white-wash shimmer: twice per word slot a soft highlight
    sweeps left to right across the glyphs, peaking around C_SUB, then
    quantized back into the palette like everything else. The wash ramp
    (five extra neutral steps between muted and text) keeps the sweep
    smooth instead of banded.
  * Seam by integer harmonics: the orbit completes orbit_revs revolutions
    per loop (an 8 s period), the spinner spin_revs (1 rev/s), and the
    word index is integer math on the frame number -- frame N reproduces
    frame 0 exactly.  The script renders one extra probe frame at f=NFRAMES
    and compares raw pixels with frame 0 before saving; a mismatch is a
    bug, not a rounding artefact.
  * A full wordlist loop is thousands of frames, far more than fits in RAM
    as decoded images, so frames stream as raw RGB into ffmpeg (paletteuse
    with the exact locked palette, dither off) instead of Pillow's
    in-memory GIF assembly -- constant memory either way.
  * All randomness happens once, at build time, from the seed.  Nothing in
    draw_frame() touches the RNG, or frames would not be reproducible.
  * Text, spinner, and shimmer render at 3x on a transparent overlay
    layer cropped to the text band (numpy-vectorized shimmer),
    LANCZOS-shrunk and composited over the scene -- glyphs get true
    supersampled edges. Each frame is then quantized back to PALETTE, so fringe
    tones land on ramp steps and no stray colors exist -- with exact
    colors the quantize is the identity elsewhere, and it doubles as
    the check.
  * `--pixel 2` renders the scene at half size and NEAREST-upscales it,
    keeping the chunky look.  The spinner and both text lines are drawn
    after the upscale at full resolution, so they are never pixelated.
    `--text-scale` multiplies the auto-fit word size.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TAU = 2.0 * math.pi
NSTARS = 9
WORD = "thinkpad"  # lowercase latin: Source Code Pro has no kana (tofu risk)
ORBIT_PERIOD = 8.0  # seconds per binary revolution; the loop holds a whole count
SPIN_RATE = 1.0  # spinner revolutions per second; the loop holds a whole count
SWEEPS_PER_WORD = 2  # shimmer passes per word slot; integer, so the seam holds
OVERLAY_SS = 3  # overlay supersample: text/shimmer render 3x, shrink for smoothness
FONT_DIR = "/usr/share/fonts/adobe-source-code-pro"
FONT_CANDIDATES = [
    "SourceCodePro-Semibold.otf",
    "SourceCodePro-Bold.otf",
    "SourceCodePro-Regular.otf",
]

# ---------------------------------------------------------------- palette --
# Base six are locked entries in meta/color-scheme.md: base ground, three
# ramp steps, and text white. C_W1..C_W5 are a wash ramp local to this
# generator: even neutral steps between muted #8A8A8A and text #D4D4D4
# (subtext #B3B3B3 sits on the ramp) so the shimmer gradient resolves
# smoothly instead of banding. Quantizing each frame against this list
# makes it impossible to emit anything else.
C_BG = "#202020"
C_RING = "#2D2D2D"
C_STAR = "#3A3A3A"
C_WHITE = "#D4D4D4"
C_GREY = "#8A8A8A"
C_SUB = "#B3B3B3"
C_W1 = "#969696"
C_W2 = "#A3A3A3"
C_W3 = "#AFAFAF"
C_W4 = "#BCBCBC"
C_W5 = "#C8C8C8"

PALETTE_HEX = [
    C_BG,
    C_RING,
    C_STAR,
    C_WHITE,
    C_GREY,
    C_SUB,
    C_W1,
    C_W2,
    C_W3,
    C_W4,
    C_W5,
]


def rgb(h: str) -> tuple[int, int, int]:
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def rgba(h: str) -> tuple[int, int, int, int]:
    r, g, b = rgb(h)
    return (r, g, b, 255)


PALETTE = [rgb(h) for h in PALETTE_HEX]


# ----------------------------------------------------------------- config --
@dataclass
class Config:
    W: int
    H: int
    fps: int
    nframes: int
    cx: float = 0.0
    cy: float = 0.0
    radius: float = 0.0
    phase: float = 0.0
    direction: int = 1  # +1 clockwise, -1 counter; harmonic 1 either way
    orbit_revs: int = 1  # binary revolutions per loop; integer, seam holds
    spin_revs: int = 8  # spinner revolutions per loop; integer, seam holds
    stars: list[tuple[int, int]] = field(default_factory=list)
    words: list[str] = field(default_factory=list)
    font_main: ImageFont.FreeTypeFont | None = None
    font_sub: ImageFont.FreeTypeFont | None = None


# ------------------------------------------------------------------ frame --
def word_at(f: int, cfg: Config) -> str:
    n = len(cfg.words)
    return cfg.words[(n * f) // cfg.nframes % n]


def text_block(cfg: Config, f1, f2, f: int):
    """thinkpad over `word...` with a small loading spinner beside it.  The
    visible spinner+word row is centered on the screen every frame, so
    short words sit centered (the row re-centers on word switches).  Word
    index is integer math on the frame number, so frame N matches frame 0
    exactly.  Returns (lines, (sx, sy, rr)): lines are (text, font, x, y,
    anchor, color); the spinner geometry is drawn separately as ring +
    rotating arc."""
    line2 = f"{word_at(f, cfg)}..."
    b1 = f1.getbbox(WORD)
    b2 = f2.getbbox(line2)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    gap = h1 // 3 + 2
    y0 = cfg.H / 2 - (h1 + gap + h2) / 2
    rr = max(2, int(round(h2 * 0.35)))
    w = b2[2] - b2[0]
    sx = cfg.cx - (rr * 2 + gap + w) / 2 + rr
    tx = sx + rr + gap
    y2 = y0 + h1 + gap + h2 / 2
    return [
        (WORD, f1, cfg.cx, y0 + h1 / 2, "mm", C_SUB),
        (line2, f2, tx, y2, "lm", C_GREY),
    ], (sx, y2, rr)


def draw_overlay(img: Image.Image, f: int, cfg: Config, ov: Config) -> None:
    """Spinner ring + rotating arc and both text lines with shimmer, all
    rendered at OVERLAY_SS x on a transparent layer cropped to the text
    band, then LANCZOS-shrunk and composited over the scene -- glyphs
    get true supersampled edges instead of single-size AA, without
    paying for a fullscreen hi-res layer. The per-frame quantize then
    pulls all fringe tones back into the palette."""
    lines, (sx, sy, rr) = text_block(ov, ov.font_main, ov.font_sub, f)
    (t1, f1, x1, y1, a1, _c1), (t2, f2, x2, y2, a2, c2) = lines
    bb1 = f1.getbbox(t1, anchor=a1)
    bb2 = f2.getbbox(t2, anchor=a2)
    os_ = OVERLAY_SS
    pad = 4 * os_
    rx0 = int(math.floor(min(x1 + bb1[0], x2 + bb2[0], sx - rr) - pad) // os_ * os_)
    ry0 = int(math.floor(min(y1 + bb1[1], y2 + bb2[1], sy - rr) - pad) // os_ * os_)
    rx1 = int(math.ceil(max(x1 + bb1[2], x2 + bb2[2], sx + rr) + pad) // os_ * os_)
    ry1 = int(math.ceil(max(y1 + bb1[3], y2 + bb2[3], sy + rr) + pad) // os_ * os_)
    rx0, ry0 = max(0, rx0), max(0, ry0)
    rx1, ry1 = min(ov.W, rx1), min(ov.H, ry1)
    layer = Image.new("RGBA", (rx1 - rx0, ry1 - ry0), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(
        [sx - rx0 - rr, sy - ry0 - rr, sx - rx0 + rr, sy - ry0 + rr],
        outline=rgba(C_STAR),
        width=os_,  # == 1px after shrinking
    )
    start = math.degrees((TAU * cfg.spin_revs * f / cfg.nframes) % TAU)
    d.arc(
        [sx - rx0 - rr, sy - ry0 - rr, sx - rx0 + rr, sy - ry0 + rr],
        start=start,
        end=start + 100,
        fill=rgba(C_WHITE),
        width=os_,
    )
    d.text((x1 - rx0, y1 - ry0), t1, font=f1, fill=rgba(C_SUB), anchor=a1)
    _draw_shimmer_text(layer, t2, f2, x2 - rx0, y2 - ry0, a2, c2, f, ov)
    small = layer.resize(((rx1 - rx0) // os_, (ry1 - ry0) // os_), Image.LANCZOS)
    img.paste(small, (rx0 // os_, ry0 // os_), small)


SHIMMER_WASH = 0.7  # peak blend of the travelling highlight toward white


def _draw_shimmer_text(
    img: Image.Image,
    text: str,
    font,
    tx: float,
    y2: float,
    anchor: str,
    col: str,
    f: int,
    cfg: Config,
) -> None:
    """Subtext line with a white-wash shimmer sweeping left to right
    twice per word slot. Sweep phase is pure integer math on the frame
    number, so frame N matches frame 0 exactly. Blends are quantized
    back into the palette by the caller. Targets a transparent RGBA
    layer: ink is written opaque, coverage handled by the mask blend."""
    bb = font.getbbox(text, anchor=anchor)
    x0 = int(math.floor(tx + bb[0])) - 2
    x1 = int(math.ceil(tx + bb[2])) + 2
    y0 = int(math.floor(y2 + bb[1])) - 2
    y1 = int(math.ceil(y2 + bb[3])) + 2
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).text(
        (tx - x0, y2 - y0), text, font=font, fill=255, anchor=anchor
    )
    n = len(cfg.words)
    phase = ((n * SWEEPS_PER_WORD * f) / cfg.nframes) % 1.0
    span_l, span_r = x0 - 20, x1 + 20
    c = span_l + (span_r - span_l) * phase
    w = max(8.0, (bb[3] - bb[1]) * 3.0)
    base, wash = rgb(col), rgb(C_WHITE)
    m = np.asarray(mask, dtype=np.float32) * (1.0 / 255.0)
    if not np.any(m):
        return
    xs = np.arange(x0, x1, dtype=np.float32)
    s = np.exp(-(((xs - c) / w) ** 2)).astype(np.float32)
    env = math.sin(math.pi * phase) ** 2  # fade to zero at the wrap so the reset is invisible
    base_a = np.array(base, dtype=np.float32)
    tgt = (
        base_a[None, :]
        + (np.array(wash, dtype=np.float32) - base_a)[None, :]
        * (SHIMMER_WASH * env * s)[:, None]
    )
    bg = np.asarray(img.crop((x0, y0, x1, y1)), dtype=np.float32)
    a = m[..., None]
    out = np.empty_like(bg)
    out[..., :3] = bg[..., :3] * (1.0 - a) + tgt[None, :, :] * a
    out[..., 3] = 255.0
    img.paste(Image.fromarray(out.astype(np.uint8), "RGBA"), (x0, y0))


def draw_frame(img: Image.Image, p: float, cfg: Config) -> None:
    d = ImageDraw.Draw(img)
    for sx, sy in cfg.stars:
        d.rectangle([sx, sy, sx + 1, sy + 1], fill=rgb(C_STAR))
    r = int(round(cfg.radius))
    d.ellipse([cfg.cx - r, cfg.cy - r, cfg.cx + r, cfg.cy + r], outline=rgb(C_RING))
    ang = cfg.phase + cfg.direction * TAU * cfg.orbit_revs * p
    u = cfg.H / 1080.0
    rw = max(2, int(round(3.0 * u)))
    rg = max(1, int(round(2.0 * u)))
    for k, (rad, col) in enumerate(((rw, C_WHITE), (rg, C_GREY))):
        a = ang + k * math.pi  # opposite ends: a true binary
        x, y = cfg.cx + r * math.cos(a), cfg.cy + r * math.sin(a)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=rgb(col))


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_CANDIDATES:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(f"no Source Code Pro found in {FONT_DIR}")


def autofit_font(cfg: Config, scale: float = 1.0) -> ImageFont.FreeTypeFont:
    """Largest size whose width stays inside the ring (70% of diameter)."""
    probe = load_font(100)
    box = probe.getbbox(WORD)
    w0 = box[2] - box[0]
    return load_font(max(8, int(round(100 * (1.4 * cfg.radius) / w0 * scale))))


def load_words() -> list[str]:
    try:
        lines = Path(__file__).with_name("spinner_words.txt").read_text().splitlines()
    except OSError:
        return ["dreaming"]
    words = [w.strip().lower() for w in lines if w.strip() and w.strip().isascii()]
    return words or ["dreaming"]


def sub_font(f1: ImageFont.FreeTypeFont) -> ImageFont.FreeTypeFont:
    return load_font(max(8, int(round(f1.size * 0.55))))


def quantize(img: Image.Image, pal_img: Image.Image) -> Image.Image:
    return img.quantize(palette=pal_img, dither=Image.Dither.NONE)


# ------------------------------------------------------------------- main --
def report(path: str, nframes: int, fps: int) -> None:
    first = Image.open(path).convert("RGB")
    colors = first.getcolors(4096) or []
    print(
        f"  saved     {path} ({os.path.getsize(path) / 1024:.0f} KB)", file=sys.stderr
    )
    print(
        f"  stored    {nframes} frames, {nframes / fps:.2f} s playing time",
        file=sys.stderr,
    )
    print(
        f"  frame 0   {len(colors)} distinct colors (palette has {len(PALETTE)})",
        file=sys.stderr,
    )


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Binary orbit GIF for awww.")
    ap.add_argument("out", help='output .gif, or "-" for stdout')
    ap.add_argument("seed", type=int)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="loop length; default len(wordlist) * --word-seconds",
    )
    ap.add_argument(
        "--word-seconds",
        type=float,
        default=3.0,
        help="seconds each status word stays up",
    )
    ap.add_argument("--no-check", action="store_true", help="skip the seam probe")
    ap.add_argument(
        "--pixel",
        type=int,
        default=1,
        help="scene render divisor; 2 = chunky 2x2 blocks",
    )
    ap.add_argument(
        "--text-scale", type=float, default=1.0, help="word size multiplier"
    )
    args = ap.parse_args(argv)

    if args.word_seconds <= 0:
        ap.error("--word-seconds must be > 0")
    words_all = load_words()
    seconds = (
        args.seconds if args.seconds is not None else len(words_all) * args.word_seconds
    )
    if seconds <= 0:
        ap.error("--seconds must be > 0")

    nframes = max(2, int(round(args.fps * seconds)))
    cfg = Config(W=args.width, H=args.height, fps=args.fps, nframes=nframes)
    cfg.orbit_revs = max(1, int(round(seconds / ORBIT_PERIOD)))
    cfg.spin_revs = max(1, int(round(seconds * SPIN_RATE)))

    t0 = time.time()
    rng = random.Random(args.seed)
    cfg.cx = cfg.W * (0.5 + rng.uniform(-0.04, 0.04))
    cfg.cy = cfg.H / 2  # orbit shares the screen's vertical middle with the text
    cfg.radius = min(cfg.W, cfg.H) * rng.uniform(0.16, 0.22)
    cfg.phase = rng.uniform(0, TAU)
    cfg.direction = rng.choice([1, -1])
    cfg.stars = [
        (rng.randint(0, cfg.W - 2), rng.randint(0, cfg.H - 2)) for _ in range(NSTARS)
    ]
    cfg.words = words_all
    rng.shuffle(cfg.words)  # seeded order: every word exactly once per loop
    div = max(1, args.pixel)
    small = replace(
        cfg,
        W=cfg.W // div,
        H=cfg.H // div,
        cx=cfg.cx / div,
        cy=cfg.cy / div,
        radius=cfg.radius / div,
        stars=[(sx // div, sy // div) for sx, sy in cfg.stars],
    )
    ov = replace(
        cfg,
        W=cfg.W * OVERLAY_SS,
        H=cfg.H * OVERLAY_SS,
        cx=cfg.cx * OVERLAY_SS,
        cy=cfg.cy * OVERLAY_SS,
        radius=cfg.radius * OVERLAY_SS,
    )
    ov.font_main = autofit_font(ov, args.text_scale)
    ov.font_sub = sub_font(ov.font_main)

    pal_img = Image.new("P", (1, 1))
    # Pad by repeating the palette, not with zeros: Pillow treats every one
    # of the 256 slots as a quantization candidate.
    flat = [c for col in PALETTE for c in col]
    pal_img.putpalette((flat * ((768 // len(flat)) + 1))[:768])

    bg = Image.new("RGB", (small.W, small.H), rgb(C_BG))
    first_bytes = b""
    probe_bytes = b""

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg not found: streaming assembly needs it")
    to_stdout = args.out == "-"
    with tempfile.TemporaryDirectory(prefix="orbit-pal-") as tmp:
        pal_path = os.path.join(tmp, "palette.png")
        # paletteuse demands exactly 256 pixels: our six colors, repeated.
        pal_small = Image.new("RGB", (256, 1))
        pal_small.putdata([PALETTE[i % len(PALETTE)] for i in range(256)])
        pal_small.save(pal_path)
        cmd = [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{cfg.W}x{cfg.H}",
            "-framerate",
            str(cfg.fps),
            "-i",
            "-",
            "-i",
            pal_path,
            "-lavfi",
            "paletteuse=dither=none",
            "-loop",
            "0",
            "pipe:1" if to_stdout else args.out,
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE if to_stdout else None,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin is not None
        # nframes + 1: the last one is the seam probe (p = 1.0 == 0.0),
        # never saved.
        for f in range(nframes + (0 if args.no_check else 1)):
            p = (f / nframes) % 1.0
            img = bg.copy()
            draw_frame(img, p, small)
            final = img.resize((cfg.W, cfg.H), Image.NEAREST)
            draw_overlay(final, f, cfg, ov)
            final = quantize(final, pal_img)
            if f == nframes:
                probe_bytes = final.tobytes()
                break
            if f == 0:
                first_bytes = final.tobytes()
            try:
                proc.stdin.write(final.convert("RGB").tobytes())
            except BrokenPipeError:
                _, err = proc.communicate()
                raise SystemExit(f"ffmpeg pipe broke: {err.decode().strip()}")
        proc.stdin.close()
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise SystemExit(f"ffmpeg failed: {err.decode().strip()}")
        if to_stdout:
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.flush()

    if not args.no_check:
        if probe_bytes != first_bytes:
            print(
                "ERROR: frame[nframes] != frame[0] -- loop is not seamless",
                file=sys.stderr,
            )
            return 2
        print("  seam      frame[N] == frame[0], pixel-identical", file=sys.stderr)

    print(
        f"  orbit     seed {args.seed}: thinkpad + "
        f"{len(cfg.words)} words ({cfg.words[0]}...), "
        f"{seconds:.1f}s loop, orbit x{cfg.orbit_revs}, "
        f"spinner x{cfg.spin_revs}",
        file=sys.stderr,
    )
    print(
        f"  rendered  {nframes} frames @ {cfg.W}x{cfg.H}, {cfg.fps} fps "
        f"in {time.time() - t0:.1f} s",
        file=sys.stderr,
    )
    if args.out != "-":
        report(args.out, nframes, cfg.fps)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
