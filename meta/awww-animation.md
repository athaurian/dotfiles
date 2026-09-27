# Animated wallpapers: Python to awww

This document describes the repository's frame-generated wallpaper workflow:
Python/Pillow produces a GIF, and `awww` displays and loops it on Sway.

## Runtime model

`awww` accepts animated GIFs as wallpaper inputs. The daemon decodes the GIF,
compresses the frames, and loops the result from memory. The workflow is:

```text
Python generator -> GIF -> `awww img` -> awww daemon
```

A live generated wallpaper therefore means generating a new GIF and setting it
again. It is not a video stream or a frame-by-frame pipe.

## Setting an animation

Use:

```sh
awww img --transition-type none <path>
awww query
```

`--transition-type none` avoids a transition competing with the animation. After
every set, use `awww query` to verify the actual displayed state.

`--resize` defaults to `crop`. Prefer generating at the output's native
resolution, which can be obtained from `awww query`, so `awww` does not have to
upscale the image. For pixel art that must be enlarged, perform the scaling with
nearest-neighbor interpolation before saving the GIF.

## Replacing the animation

Use a new filename for each generated GIF:

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

Do not repeatedly set the same path. The daemon caches by path, so reusing a
filename can replay previously decoded frames. Remove the previous file only
after the new animation has been set.

Leave enough time between generations for rendering to finish. The measured
render times below make a one-minute interval a comfortable starting point.

## Reboots and session startup

The normal Sway startup path sets a still wallpaper. Consequently, a generated
animation loop started manually does not persist across reboot by itself.

An animation that must start with the Sway session needs a user service attached
to the compositor session target, following the same session dependency model as
the repository's existing wallpaper daemon service.

## GIF constraints

### Frame timing

GIF frame delays use centiseconds. For example, `125 ms` is stored at about
`12 cs`. Do not compensate for this small quantization effect by altering the
intended animation timing unless the resulting playback has a measured problem.

### Palette size

GIF supports at most 256 colors. Generated wallpapers should use colors from
`meta/color-scheme.md`.

Create a Pillow palette from the locked repository colors and quantize every
frame against it:

```python
pal = Image.new("P", (1, 1))
pal.putpalette(
    [c for rgb in PALETTE for c in rgb]
    + [0] * (768 - 3 * len(PALETTE))
)
q = frame.quantize(palette=pal, dither=Image.Dither.NONE)
```

No dithering keeps flat areas flat and prevents generated frames from acquiring
colors outside the palette.

### Frame merging

Pillow may merge consecutive identical frames and add their durations together.
The encoded GIF can therefore contain fewer frames than the generator produced.

Do not use encoded frame count as the proof of loop correctness. Compare frame
pixels when checking whether a loop closes as intended, for example with
`frame.tobytes()`.

### Looping

Use `loop=0` for an animation that repeats indefinitely.

Two loop structures are reliable:

| Structure      | Requirement                                                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Seamless cycle | Complete whole periods of any oscillation within the loop so the last frame transitions naturally to the first.               |
| Grow and hold  | Render the action once, then encode one final frame with a long duration instead of rendering repeated identical hold frames. |

A repeated hold does not need to be rendered as many identical frames because
Pillow can merge them. A loop restart is still a hard cut; a long final hold can
make that cut read as a new scene rather than an accidental glitch.

## Performance characteristics

Rendering cost scales primarily with the number of primitives drawn across all
frames. The daemon's runtime cost is comparatively stable once the GIF is
cached.

| Experiment                  | Frames | Resolution     |    Size | Generation | Daemon        |
| --------------------------- | -----: | -------------- | ------: | ---------: | ------------- |
| Swaying tree, 12 fps        |     24 | 640×360        |   33 KB |      0.5 s | 0.0% / ~20 MB |
| Tree lifecycle, 10 fps      |   ~180 | 1920×1080      | ~400 KB |      ~22 s | 0.0% / ~19 MB |
| Single life + death, 8 fps  |    224 | 1920×1080      |  671 KB |      ~22 s | 0.0% / ~19 MB |
| cbonsai port, growth + hold |     46 | 1920×1080 text |  408 KB |       14 s | 0.0% / ~19 MB |

PIL text rendering was the slowest measured workload. About 15,000 cells across
roughly 10 frames took 15–20 seconds. For text-heavy animations, draw only
occupied cells.

## Validation

Most structural properties can be checked without watching the complete
animation:

1. **Inspect the GIF with Pillow.** Check durations, total playback time, and
   distinct colors.
2. **Inspect color distribution.** Count pixels per palette color per frame and
   compare successive stages of the animation. For text art, use full-frame
   NumPy masks rather than sparse sampling because thin glyphs are easy to miss.
3. **Verify the daemon state.** Run `awww query` after setting the animation.
4. **Check resource usage.** Inspect `awww-daemon` with `ps` while testing.
5. **Watch one complete loop.** Structure can be verified programmatically, but
   pacing and visual density still require visual inspection.

## Generator skeleton

A deterministic frame generator should derive each frame from its frame index
and seed. A minimal implementation is:

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
    """Draw frame f (0-based) of nframes deterministically."""
    t = 2 * math.pi * f / nframes
    cx = W / 2 + int(200 * math.sin(t))
    draw.ellipse(
        [cx - 40, H / 2 - 40, cx + 40, H / 2 + 40],
        fill=FG,
    )


def main(out, seed):
    rng = random.Random(seed)
    nframes = FPS * 6
    frames = []

    for f in range(nframes):
        img = Image.new("RGB", (W, H), BG)
        draw_frame(ImageDraw.Draw(img), f, nframes, rng)
        frames.append(img)

    pal = Image.new("P", (1, 1))
    pal.putpalette(
        [c for rgb in PALETTE for c in rgb]
        + [0] * (768 - 3 * len(PALETTE))
    )
    quantized = [
        frame.quantize(palette=pal, dither=Image.Dither.NONE)
        for frame in frames
    ]
    quantized[0].save(
        out,
        save_all=True,
        append_images=quantized[1:],
        duration=int(1000 / FPS),
        loop=0,
    )


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
```

The skeleton sweeps a full period per loop, keeping the cycle continuous at the
seam.

Extend the skeleton rather than treating it as a production animation framework.

## Repository colors

Generated artwork follows the same palette boundary as application
configuration: every color comes from `meta/color-scheme.md`.

A new hue must be added to the normal palette workflow before it is used, even
for experimental animation.

## Common failure modes

| Failure                                           | Prevention                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Reusing a GIF path replays stale frames           | Generate a unique filename for each animation.                                       |
| Pillow merges identical frames                    | Validate playback duration or pixels, not encoded frame count.                       |
| GIF timing is slightly shorter than intended      | Treat centisecond quantization as expected unless measured playback is unacceptable. |
| Small artwork becomes blurry                      | Render at native output size or scale with nearest-neighbor before saving.           |
| Wallpaper transitions interfere with animation    | Use `--transition-type none`.                                                        |
| Oscillation jumps at the loop seam                | Fit complete periods into the loop and compare head/tail frames.                     |
| Assumed wallpaper differs from the actual display | Verify with `awww query`.                                                            |
| Animation disappears after reboot                 | Start it from the Sway session when persistence is required.                         |
