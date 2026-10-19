# Screenshot capture

The desktop images in `docs/images/` come from the live Sway session, not a
headless renderer. `meta/hero.py` cuts and composes the split pairs, and
`meta/palette-card.py` renders the palette card. The capture steps take over the
session, so run them by hand in order.

## Rules

- Switch to workspace 3 before starting. `swaymsg exec` uses the focused
  workspace, so start programs there.
- foot reads its configuration at startup. To capture both modes, switch modes
  and start fresh foot processes instead of reusing them.
- The hero pair uses the `hero-nvim` and `hero-term` app IDs so the kill steps
  can target them.
- Start nvim with `--listen` so the remote commands can clear the prompt and
  recenter the buffer. If pyright fails at startup, nvim shows a press-Enter
  prompt that blocks `--remote-expr`. Clear it with `--remote-send '<Esc><CR>'`
  first.
- Focus `hero-nvim` after both panes exist so the border and cursor land in the
  right pane.
- Close notifications with `dunstctl close-all` before every `grim` command.
- `grim` captures the display at its current resolution, so full-screen shots
  are 1920x1080.
- Restore the session at the end: dark mode, workspace 1, no `hero-*` or
  `fuzzel` processes, and no nvim socket.

The active mode is recorded in `~/.local/state/palette-mode`. Check it before
starting with `cat ~/.local/state/palette-mode`.

## Outputs

The following table lists each image and its source.

| Image                        | Source                                         |
| ---------------------------- | ---------------------------------------------- |
| `hero.webp`                  | `stage-light.png` + `stage-dark.png`, composed |
| `hero-empty.webp`            | `empty-light.png` + `empty-dark.png`, composed |
| `picker-launcher.webp`       | `menu-launcher.png`, cropped                   |
| `picker-launcher-light.webp` | `menu-launcher-light.png`, cropped             |
| `picker-poweroff.webp`       | `menu-poweroff.png`, cropped                   |
| `picker-poweroff-light.webp` | `menu-poweroff-light.png`, cropped             |
| `lock.webp`                  | `lock-dark.png`                                |
| `lock-light.webp`            | `lock-light.png`                               |
| `palette.webp`               | `meta/palette-card.py`, no capture             |

Staging files go in `/tmp/chezmoi-shots/` and can be discarded.

## Hero pair

The following block captures light mode. Repeat it with `palette-mode dark` and
`stage-dark.png` for the dark capture:

```sh
~/.local/bin/palette-mode light
swaymsg workspace 3
rm -f /tmp/chezmoi-shots/nvim-hero.sock
swaymsg exec "foot -a hero-nvim nvim --listen /tmp/chezmoi-shots/nvim-hero.sock -c 'normal! zR' -c 'normal! 330Gzz' $HOME/.local/share/chezmoi/assets/hl_test.py"
sleep 0.4
swaymsg exec "foot -a hero-term sh -c 'python3 $HOME/.local/share/chezmoi/assets/hl_test.py; exec sh'"
sleep 0.6
swaymsg '[app_id=hero-nvim] focus'
sleep 11
timeout 5 nvim --server /tmp/chezmoi-shots/nvim-hero.sock --remote-send '<Esc><CR>'
timeout 8 nvim --server /tmp/chezmoi-shots/nvim-hero.sock --remote-expr 'execute("normal! 330Gzz")'
dunstctl close-all
grim /tmp/chezmoi-shots/stage-light.png
swaymsg '[app_id=hero-nvim] kill'
swaymsg '[app_id=hero-term] kill'
rm -f /tmp/chezmoi-shots/nvim-hero.sock
```

Compose the pair with:

```sh
uv run --with pillow python3 meta/hero.py /tmp/chezmoi-shots/stage-light.png \
  /tmp/chezmoi-shots/stage-dark.png -o docs/images/hero.webp
```

By default, the divider runs from 0.75 of the width at the top to 0.25 at the
bottom. The dark capture fills the top, and the light capture fills the bottom.
The output keeps the source resolution, with an anti-aliased edge and no
separator line.

## Empty desktop pair

Start with no windows open and no nvim socket. Flip modes between captures:

```sh
~/.local/bin/palette-mode light
swaymsg workspace 3
dunstctl close-all
sleep 2
grim /tmp/chezmoi-shots/empty-light.png
```

Repeat with `palette-mode dark` and `empty-dark.png`, then compose with the same
`meta/hero.py` command as the hero pair.

## Pickers

Capture the launcher and power menu in both modes. The following steps start in
dark mode. Repeat them in light mode with the `-light` filenames.

```sh
~/.local/bin/palette-mode dark
swaymsg workspace 3
dunstctl close-all
swaymsg exec fuzzel
sleep 1.5
dunstctl close-all
grim /tmp/chezmoi-shots/menu-launcher.png
pkill -x fuzzel
```

```sh
swaymsg exec "$HOME/.config/sway/scripts/power_control.sh poweroff"
sleep 1.5
dunstctl close-all
grim /tmp/chezmoi-shots/menu-poweroff.png
pkill -x fuzzel
rm -f "${XDG_RUNTIME_DIR}/confirm_action"
```

Do not use a `pkill -f` pattern that mentions the fuzzel confirmation prompt in
the invoking command line. `power_control.sh` matches that pattern against full
command lines and kills the caller. Use `pkill -x fuzzel` to cancel both menus.

Both modes use the same 752x498 frame, centered on each menu's bounding-box
center. The offsets come from a difference against the empty capture for that
mode, with the bar rows excluded:

```sh
for suffix in "" "-light"; do
  magick "/tmp/chezmoi-shots/menu-launcher${suffix}.png" -crop 752x498+581+307 +repage \
    -quality 90 "docs/images/picker-launcher${suffix}.webp"
  magick "/tmp/chezmoi-shots/menu-poweroff${suffix}.png" -crop 752x498+581+305 +repage \
    -quality 90 "docs/images/picker-poweroff${suffix}.webp"
done
```

If the menu changes size, recompute the frame:

```sh
magick /tmp/chezmoi-shots/menu-launcher.png /tmp/chezmoi-shots/empty-dark.png \
  -compose difference -composite -crop 1920x1040+0+40 +repage \
  -threshold 8% -trim info:
```

The output is the menu's bounding box in the cropped canvas. Add 40 pixels to
the y coordinate, center a 752x498 frame on the box, and use that frame's
offsets. Use `empty-light.png` when recomputing the light frames.

## Lock screen

`lock.sh` shows a 2.5-second warning, blurs a snapshot of the desktop, then
starts swaylock. `grim` captures the locked screen 8 seconds later. Unlock it
yourself afterward.

```sh
swaymsg workspace 3
dunstctl close-all
( sleep 8; grim /tmp/chezmoi-shots/lock-dark.png ) &
~/.config/sway/scripts/lock.sh
```

Wait 15 seconds at the password prompt before unlocking. For light mode, repeat
the capture and save it as `lock-light.png`. Convert both captures:

```sh
magick /tmp/chezmoi-shots/lock-dark.png -quality 88 docs/images/lock.webp
magick /tmp/chezmoi-shots/lock-light.png -quality 88 docs/images/lock-light.webp
```

## Palette card

Render the palette card from the derived palette. It needs no session capture:

```sh
uv run --with pillow python3 meta/palette-card.py
```

## Themed images

The picker and lock figures include both captures. The light URL ends in
`#only-light` and the dark URL in `#only-dark`. Zensical hides the variant that
does not match the active scheme. The GLightbox `auto_themed` option in
`zensical.toml` keeps the hidden variant out of the gallery.

The hero pairs and the palette card intentionally show both modes, so they stay
visible in either scheme and carry no fragment.

## Checks

Run these from the repository root:

```sh
make lint
make site
python3 -m http.server 8000 --directory site
```

The build copies the images to `site/images/` and wraps each one in a lightbox
link.
