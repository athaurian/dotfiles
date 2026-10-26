# Screenshot capture

The desktop images in `docs/images/` come from a live Sway session, not a
headless renderer. The scripts in `meta/shots/` capture the screen and crop or
compose the published figures. Run them by hand because they take over the
session.

Run these commands from the repository root. Pass `--help` to a script to list
its actions.

For a complete refresh of every capture that does not need manual intervention,
run `meta/shots/redo-all.sh`. It covers the hero pair through the palette card
and restores dark mode on workspace 1. It does not touch the lock or Discord
captures.

## Before capturing

Most scripts set the palette, switch to the workspace they need, close
notifications, and close the windows they open. Some captures need manual setup:

- Close all windows and remove `/tmp/chezmoi-shots/nvim-hero.sock` for the empty
  desktop pair.
- Open a fresh kitty for each editor mode so the palette is current, and focus
  the editor before capturing.
- Close notifications before a manual `grim`.
- Save the Discord captures as full-screen PNGs in `meta/captures/`.

Full-screen captures are 1920x1080 because `grim` uses the current display
resolution.

For manual captures, check the active mode with:

```sh
cat ~/.local/state/palette-mode
```

When done, switch back to dark mode, return to your starting workspace, close
any leftover `hero-*` windows, stop `fuzzel`, and remove
`/tmp/chezmoi-shots/nvim-hero.sock`.

## Closing capture windows

`swaymsg ... kill` sends a close request. Kitty asks for confirmation when a
program is running, so the window stays open. The scripts read the kitty PID
from the Sway tree and send `SIGTERM`. `SIGKILL` is only a fallback.

## Outputs

The following table lists each image and its source.

| Image                         | Source                                          |
| ----------------------------- | ----------------------------------------------- |
| `hero.webp`                   | `stage-light.png` + `stage-dark.png`, composed  |
| `hero-empty.webp`             | `empty-light.png` + `empty-dark.png`, composed  |
| `og.png`                      | `editor-light.png` + `empty-dark.png`, composed |
| `picker-launcher.webp`        | `menu-launcher.png`, cropped                    |
| `picker-launcher-light.webp`  | `menu-launcher-light.png`, cropped              |
| `picker-poweroff.webp`        | `menu-poweroff.png`, cropped                    |
| `picker-poweroff-light.webp`  | `menu-poweroff-light.png`, cropped              |
| `picker-clipboard.webp`       | `picker-clipboard.png`, border crop             |
| `picker-clipboard-light.webp` | `picker-clipboard-light.png`, border crop       |
| `lock.webp`                   | `lock-dark.png`                                 |
| `lock-light.webp`             | `lock-light.png`                                |
| `bar.webp`                    | `bar-dark.png`, top 24 pixels                   |
| `bar-light.webp`              | `bar-light.png`, top 24 pixels                  |
| `neovim-editor.webp`          | `editor-dark.png`, cropped                      |
| `neovim-editor-light.webp`    | `editor-light.png`, cropped                     |
| `neovim-discord.webp`         | `discord-dark.png`, cropped to the card border  |
| `neovim-discord-light.webp`   | `discord-light.png`, cropped to the card border |
| `palette.webp`                | `meta/shots/palette.py`, rendered               |

Raw captures stay in `meta/captures/` with their geometry where needed. Rebuild
`og.png` with `make social`.

## Hero pair

Capture one mode at a time:

```sh
meta/shots/hero.py light
meta/shots/hero.py dark
```

The script sets the palette, switches to workspace 3, and opens nvim and a
terminal. It waits 11 seconds for nvim to start. If pyright fails at startup,
nvim waits at a prompt for Enter. The script clears it with `<Esc><CR>` before
recentering the buffer, writes `stage-<mode>.png`, and closes both windows.

Compose the pair with:

```sh
meta/shots/hero.py compose
```

The divider runs from 0.75 of the width at the top to 0.25 at the bottom. The
dark capture fills the top and the light capture fills the bottom. The output
keeps the source resolution, with an anti-aliased edge and no separator line.

## Empty desktop pair

Close all windows and remove the nvim socket. Capture each mode:

```sh
meta/shots/empty.py light
meta/shots/empty.py dark
```

The script sets the palette, switches to workspace 3, closes notifications,
waits ten seconds, and writes `empty-<mode>.png`. Compose the pair with:

```sh
meta/shots/empty.py compose
```

## Editor pair

Open nvim on `assets/hl_test.py` in workspace 3 with the explorer on the left.
Start at line 330, open the explorer, press `I` to show ignored files, then move
back to the editor and center the line. `assets/` is gitignored, and the
explorer hides ignored files by default.

```sh
swaymsg exec "kitty --class editor-nvim nvim +330 assets/hl_test.py"
```

In nvim, run `:lua Snacks.explorer()`, press `I`, then `<C-w>l` and `330Gzz`.
Capture each mode:

```sh
meta/shots/editor.py dark
meta/shots/editor.py light
```

The script focuses the `editor-nvim` window, captures `editor-<mode>.png`, and
saves the window geometry in `editor-<mode>.geom`. Compose the pair with:

```sh
meta/shots/editor.py compose
```

The compose step crops the border box with `meta/round-corners.py`. It uses a
5px radius and fills the corners with the page background (`#050505` for slate,
`#f3efec` for default). The `--edge` color is the window border. The geometry
file keeps the crop aligned when the window size changes.

## Discord pair

Capture the profile card in both modes and save the full-screen images as
`meta/captures/discord-dark.png` and `meta/captures/discord-light.png`. Crop
them with:

```sh
meta/shots/discord.py dark
meta/shots/discord.py light
```

Use `compose` to crop both at once:

```sh
meta/shots/discord.py compose
```

The card sits at `432x160+960+281`, and its corners have a 12px radius. The dark
card has no border. The light card's border extends two pixels lower, so the
dark crop is `432x158+960+281`. The script fills the corners with the page
background. The edge color is the card fill for dark and the card border for
light.

## Pickers

Capture both menus in each mode:

```sh
meta/shots/pickers.py dark
meta/shots/pickers.py light
```

The script sets the palette, switches to workspace 3, captures the launcher and
power menu, and crops the four figures. It stops fuzzel with `pkill -x fuzzel`.
Avoid a broad `pkill -f` pattern; it can match the shell running the command and
kill the caller.

The crops are 752x498 and centered on the menu. If the menu size changes, use
the `frame` action:

```sh
meta/shots/pickers.py frame dark
meta/shots/pickers.py frame light
```

It prints the menu bounds in a canvas that starts 40 pixels below the top of the
screen. Add 40 to the y offset, center the 752x498 frame on the bounds, and
update the offsets in `pickers.py`. The action uses the empty capture for the
same mode.

## Clipboard history

The script seeds a throwaway database in `/tmp/chezmoi-shots/`, sets the
palette, and switches to workspace 3. The seeded entries end with
`meta/shots/clipboard-preview.webp`, so the preview shows that image when the
picker opens.

Capture each mode:

```sh
meta/shots/clipboard.py light
meta/shots/clipboard.py dark
```

The picker opens in a kitty window titled `clipboard_term`. The script shows the
window, centers it, focuses it, and captures it. It writes
`picker-clipboard<mode>.png`, closes the picker by PID with `SIGTERM`, removes
the database, and crops the figure. Use an otherwise empty workspace.

Both modes use the same border crop: `1428x728+246+188`. The corners have a 5px
radius, so a rectangular crop would keep wallpaper pixels.
`meta/round-corners.py` crops the border box, rounds the corners, and fills them
with the page background. The edge color is the window border.

Create the database without capturing with `meta/shots/clipboard.py seed`.
Recrop an existing raw with `meta/shots/clipboard.py crop light`.

## Lock screen

Capture each mode:

```sh
meta/shots/lock.py dark
meta/shots/lock.py light
```

The script schedules a capture, then runs `lock.sh` with a fixed time and date.
The lock script shows a warning for 2.5 seconds, blurs a snapshot of the
desktop, and starts `swaylock`. The capture runs 8 seconds after `lock.py`
starts. Wait at least 15 seconds before unlocking so the capture finishes.

Convert an existing raw with `meta/shots/lock.py convert light`.

## Status bar

Capture each mode:

```sh
meta/shots/bar.py light
meta/shots/bar.py dark
```

The script switches to workspace 3 and opens a preview terminal titled
`hl_test.py`. The title keeps the center module stable. It waits ten seconds for
the update module to initialize, captures the top 24 pixels, closes the preview,
and converts the strip to WebP.

Convert an existing raw with `meta/shots/bar.py crop light`.

## Palette card

The palette card needs no capture:

```sh
meta/shots/palette.py
```

## Themed images

The picker, lock, and status bar figures have light and dark versions. The light
URL ends in `#only-light` and the dark URL in `#only-dark`, so Zensical shows
the version that matches the active scheme. The GLightbox `auto_themed` option
in `zensical.toml` keeps the hidden version out of the gallery.

The hero pairs and the palette card show both modes on purpose, so they have no
fragment.

## Checks

Run these from the repository root:

```sh
make lint
make site
python3 -m http.server 8000 --directory site
```

The build copies the images to `site/images/` and wraps each one in a lightbox
link.
