# Animated wallpapers: Python → awww

Putting generated animations on screen with the `awww` wallpaper daemon.
Tested with awww 0.12.1 on Sway, one 1920×1080 output. The trees in
`/tmp/opencode/tree/` were the first tries; the same steps work for any
frame-by-frame animation.

## How it works

awww only animates GIFs. No video, no pipe for pushing frames — you hand
it a GIF with `awww img`, it decodes the frames once, compresses them,
and loops them from memory. So a "live wallpaper" really means writing
new GIF files every so often and pointing the daemon at them:

```
generator (Python + PIL) → out.gif → `awww img out.gif` → daemon loops it
```

## Setting an image

```
awww img --transition-type none <path>
awww query
```

The `none` transition swaps instantly instead of fading, which is what
you want when the file itself is the animation. There is also `--resize`
(default `crop`, scale to fill): if you render at the output's native
size — `awww query` prints the dimensions — scaling never kicks in. That
matters for pixel art, because anything smaller gets Lanczos-filtered on
the way up. If you want hard pixels, draw small and scale up with NEAREST
yourself, then save at full size. `-` reads from stdin. After every set,
check `awww query`: it prints what is actually on screen, which beats
assuming.

## Keeping it live

Render and re-set in a loop. Two things bit us:

- Give every generation its own filename (`anim-<seed>.gif`) and delete
  the old file after setting the new one. The daemon caches by path, so
  setting the same path twice can replay the old frames.
- Sleep longer than rendering takes. Ours take 5–25 seconds, so 60+
  seconds between generations is comfortable. The `awww img` call itself
  is instant.

```sh
prev=""
while true; do
  seed="$(shuf -i 1-999999 -n 1)"
  file="anim-$seed.gif"
  python3 anim.py "$file" "$seed"
  awww img --transition-type none "$file"
  [ -n "$prev" ] && rm -f "$prev"
  prev="$file"
  sleep 60
done
```

One more: `sway/config` sets a still image at login, so after a reboot
you are back to the still until the loop ticks again. If an experiment
ever deserves to survive reboots, it wants a `sway-session.target` unit
like the one `awww-daemon` has.

## GIF details worth knowing

- Frame delays work, but GIF only stores centiseconds: 125 ms lands on
  ~12 cs. A loop designed for 23.0 s measured 22.3 s. Even shrinkage,
  invisible in practice — don't chase it.
- Max 256 colors. Make a palette out of locked hexes from
  `meta/color-scheme.md` and quantize every frame against it:

  ```python
  pal = Image.new("P", (1, 1))
  pal.putpalette([c for rgb in PALETTE for c in rgb] + [0] * (768 - 3 * len(PALETTE)))
  q = frame.quantize(palette=pal, dither=Image.Dither.NONE)
  ```

  No dithering keeps flat areas flat (and small). Since every frame goes
  through the same palette, no stray colors can sneak in — which is also
  how the repo's color rule holds for generated files.
- Pillow merges consecutive identical frames and adds their durations
  together. The saved file ends up with fewer frames than you rendered;
  total playing time is unchanged. So don't assert on frame counts — if
  you need to prove a seamless loop, compare pixels (`tobytes()`).
- Files stay small. Flat color compresses well: a 176-frame 1080p
  animation was 394 KB, 46 frames of full-screen text 408 KB. The daemon
  sat at ~19 MB and 0% CPU through all of it.
- `loop=0` repeats forever.
- Two loop shapes that work. A seamless cycle, where the last frame flows
  back into the first: anything oscillating has to complete whole periods
  inside the loop, and comparing head and tail frames in code catches
  mistakes before you watch anything. Or grow-and-hold: normal frames for
  the action, then a single final frame with a long duration (3–6 s)
  instead of rendering the hold over and over. The restart is a hard cut
  either way; the hold makes it feel like a fresh scene rather than a
  glitch. (Pillow would merge repeated holds anyway — don't render them.)

## Colors

Same rule as the app configs: every hex comes from
`meta/color-scheme.md`. With generated art this is easy to guarantee —
the `PALETTE` list only holds locked hexes, and quantization makes
anything else impossible to emit. The greys plus one hue (green `#89C952` /
`#B9EE7D` over `diff-add` `#2B4218`, red `#FE4864`) go a long way. If you need a new hue, it goes through the
normal route first — doc, `meta/palette.py`, paste — even for throwaways.

## Checking your work without watching it

Most of a render can be verified blind:

1. Open the GIF with PIL: frame count, durations added up (playing time),
   distinct colors per frame.
2. Count pixels per color per frame and box them in. That traces the
   staging: canopy color staying high while the seed color sits next to
   it, then collapsing, tells you the handoff happened in the right
   order. Sample every Nth pixel for speed — except with text art, where
   sampling skips over thin glyphs and full-frame numpy masks are safer.
3. `awww query` after each set, `ps` on `awww-daemon` for cost.
4. Then watch one full loop. The checks above catch structure; pacing and
   density still need eyes.

## What things cost

| Experiment | Frames | Res | Size | Gen time | Daemon |
|---|---|---|---|---|---|
| Swaying tree, 12 fps | 24 | 640×360 | 33 KB | 0.5 s | 0.0% / ~20 MB |
| Tree lifecycle, 10 fps | ~180 | 1920×1080 | ~400 KB | ~22 s | 0.0% / ~19 MB |
| Single life + death, 8 fps | 224 | 1920×1080 | 671 KB | ~22 s | 0.0% / ~19 MB |
| cbonsai port, growth+hold | 46 | 1920×1080 text | 408 KB | 14 s | 0.0% / ~19 MB |

Drawing cost grows with primitives times frames; the daemon costs the
same once the file is cached. The slowest thing measured was PIL text:
~15k cells over ~10 frames took 15–20 s. Draw only cells that have
something in them.

## Starter script

```python
#!/usr/bin/env python3
"""anim.py OUT SEED -- generic awww animation skeleton."""
import math
import random
import sys
from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 8
BG = (0x20, 0x20, 0x20)
FG = (0xD4, 0xD4, 0xD4)
PALETTE = [BG, FG]

def draw_frame(draw, f, nframes, rng):
    """Draw frame f (0-based) of nframes. Deterministic in f."""
    t = 2 * math.pi * f / nframes  # full periods only: seamless loop
    cx = W / 2 + int(200 * math.sin(t))
    draw.ellipse([cx - 40, H / 2 - 40, cx + 40, H / 2 + 40], fill=FG)

def main(out, seed):
    rng = random.Random(seed)
    nframes = FPS * 6  # 6 s seamless loop
    frames = []
    for f in range(nframes):
        img = Image.new("RGB", (W, H), BG)
        draw_frame(ImageDraw.Draw(img), f, nframes, rng)
        frames.append(img)
    pal = Image.new("P", (1, 1))
    pal.putpalette([c for rgb in PALETTE for c in rgb] + [0] * (768 - 6))
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(out, save_all=True, append_images=q[1:],
              duration=int(1000 / FPS), loop=0)

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
```

Then: `python3 anim.py /tmp/anim-1.gif 1 && awww img --transition-type none
/tmp/anim-1.gif && awww query`.

## Mistakes already made

- Setting the same path twice can replay stale frames → unique filenames.
- Pillow merges identical frames → check wall time, not frame counts.
- Centisecond storage shortens loops slightly → ignore it.
- Non-native art gets Lanczos upscale → render native or NEAREST.
- Transitions fight animation → `--transition-type none` for sets.
- Oscillation periods must fill the loop or the seam jumps.
- `awww query` prints what is on screen; trust it over assumptions.
- A reboot brings back the still from `sway/config`, not your loop.
