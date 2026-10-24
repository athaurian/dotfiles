# Screenshot capture

The desktop images in `docs/images/` come from the live Sway session, not a
headless renderer. The `meta/hero.py` script cuts and composes the split pairs,
and the `meta/palette-card.py` script renders the palette card. The capture
steps take over the session, so run them by hand in order.

## Rules

- Switch to workspace 3 before starting. The `swaymsg exec` command uses the
  focused workspace, so start programs there.
- Start fresh `kitty` processes for each mode instead of reusing windows, so
  each capture uses the current generated theme.
- The hero pair uses the `hero-nvim` and `hero-term` app IDs so the kill steps
  can target them.
- Start nvim with `--listen` so the remote commands can clear the prompt and
  recenter the buffer. If pyright fails at startup, nvim shows a press-Enter
  prompt that blocks `--remote-expr`. Clear it with `--remote-send '<Esc><CR>'`
  first.
- Focus `hero-nvim` after both panes exist so the border and cursor land in the
  right pane.
- Close notifications with `dunstctl close-all` before every `grim` command.
- Focus the window before `grim` when the theme dims the unfocused window, or
  the capture comes out dimmed.
- The `grim` command captures the display at its current resolution, so
  full-screen shots are 1920x1080.
- Restore the session at the end: dark mode, workspace 1, no `hero-*` or
  `fuzzel` processes, and no nvim socket.

The active mode is recorded in `~/.local/state/palette-mode`. Check it before
starting with `cat ~/.local/state/palette-mode`.

## Outputs

The following table lists each image and its source.

| Image                         | Source                                          |
| ----------------------------- | ----------------------------------------------- |
| `hero.webp`                   | `stage-light.png` + `stage-dark.png`, composed  |
| `hero-empty.webp`             | `empty-light.png` + `empty-dark.png`, composed  |
| `og.png`                      | `stage-light.png` + `empty-dark.png`, composed  |
| `picker-launcher.webp`        | `menu-launcher.png`, cropped                    |
| `picker-launcher-light.webp`  | `menu-launcher-light.png`, cropped              |
| `picker-poweroff.webp`        | `menu-poweroff.png`, cropped                    |
| `picker-poweroff-light.webp`  | `menu-poweroff-light.png`, cropped              |
| `picker-clipboard.webp`       | `picker-clipboard.png`, border crop             |
| `picker-clipboard-light.webp` | `picker-clipboard-light.png`, border crop       |
| `lock.webp`                   | `lock-dark.png`                                 |
| `lock-light.webp`             | `lock-light.png`                                |
| `bar.webp`                    | `bar-dark.png`, cropped to the bar              |
| `bar-light.webp`              | `bar-light.png`, cropped to the bar             |
| `neovim-editor.webp`          | `editor-dark.png`, cropped                      |
| `neovim-editor-light.webp`    | `editor-light.png`, cropped                     |
| `neovim-discord.webp`         | `discord-dark.png`, cropped to the card border  |
| `neovim-discord-light.webp`   | `discord-light.png`, cropped to the card border |
| `palette.webp`                | `meta/palette-card.py`, no capture              |

Raws are archived in `meta/captures/` with their crop geometry, except the lock
pair. Scratch goes in `/tmp/chezmoi-shots/` and can be discarded.

## Hero pair

The following block captures light mode. Repeat it with the `palette-mode dark`
command and `stage-dark.png` for the dark capture:

```sh
~/.local/bin/palette-mode light
swaymsg workspace 3
rm -f /tmp/chezmoi-shots/nvim-hero.sock
swaymsg exec "kitty --class hero-nvim nvim --listen /tmp/chezmoi-shots/nvim-hero.sock -c 'normal! zR' -c 'normal! 330Gzz' $HOME/.local/share/chezmoi/assets/hl_test.py"
sleep 0.4
swaymsg exec "kitty --class hero-term sh -c 'python3 $HOME/.local/share/chezmoi/assets/hl_test.py; exec sh'"
sleep 0.6
swaymsg '[app_id=hero-nvim] focus'
sleep 11
timeout 5 nvim --server /tmp/chezmoi-shots/nvim-hero.sock --remote-send '<Esc><CR>'
timeout 8 nvim --server /tmp/chezmoi-shots/nvim-hero.sock --remote-expr 'execute("normal! 330Gzz")'
dunstctl close-all
grim meta/captures/stage-light.png
swaymsg '[app_id=hero-nvim] kill'
swaymsg '[app_id=hero-term] kill'
rm -f /tmp/chezmoi-shots/nvim-hero.sock
```

Compose the pair with:

```sh
uv run --with pillow python3 meta/hero.py meta/captures/stage-light.png \
  meta/captures/stage-dark.png -o docs/images/hero.webp
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
grim meta/captures/empty-light.png
```

Repeat with the `palette-mode dark` command and `empty-dark.png`, then compose
with the same `meta/hero.py` command as the hero pair.

## Editor pair

Open nvim on `assets/hl_test.py` on workspace 3 with the explorer open on the
left. Press `I` in the explorer to list ignored files: the explorer config
leaves `ignored` off, and `assets/` is gitignored, so the file has no visible
path in the tree until then. `H` toggles hidden files, which the config already
enables and which hide the dotfiles again.

```sh
~/.local/bin/palette-mode dark
swaymsg workspace 3
dunstctl close-all
grim meta/captures/editor-dark.png
```

Repeat with the `palette-mode light` command and `editor-light.png`. The window
border box is `1904x1040+8+32`, recorded beside each raw as a `.geom` file. The
crop keeps that border and masks the corners outside it:

```sh
magick meta/captures/editor-dark.png \
  -crop 1904x1040+8+32 +repage \
  \( -size 1904x1040 xc:none -fill white \
     -draw "roundrectangle 0,0,1903,1039,4,4" \) \
  -compose DstIn -composite \
  -quality 92 docs/images/neovim-editor.webp
magick meta/captures/editor-light.png \
  -crop 1904x1040+8+32 +repage \
  \( -size 1904x1040 xc:none -fill white \
     -draw "roundrectangle 0,0,1903,1039,4,4" \) \
  -compose DstIn -composite \
  -quality 92 docs/images/neovim-editor-light.webp
```

## Discord pair

Capture the Discord profile card in both modes at full screen. Archive the
screenshots as `discord-dark.png` and `discord-light.png`. The card sits at
`432x160+960+281` in the 1920x1080 capture, recorded beside each raw as a
`.geom` file. Crop each raw to the card border and mask the corners outside it:

```sh
magick meta/captures/discord-dark.png \
  -crop 432x160+960+281 +repage \
  \( -size 432x160 xc:none -fill white \
     -draw "roundrectangle 0,0,431,159,8,8" \) \
  -compose DstIn -composite \
  -quality 92 docs/images/neovim-discord.webp
magick meta/captures/discord-light.png \
  -crop 432x160+960+281 +repage \
  \( -size 432x160 xc:none -fill white \
     -draw "roundrectangle 0,0,431,159,8,8" \) \
  -compose DstIn -composite \
  -quality 92 docs/images/neovim-discord-light.webp
```

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
grim meta/captures/menu-launcher.png
pkill -x fuzzel
```

```sh
swaymsg exec "$HOME/.config/sway/scripts/power_control.sh poweroff"
sleep 1.5
dunstctl close-all
grim meta/captures/menu-poweroff.png
pkill -x fuzzel
rm -f "${XDG_RUNTIME_DIR}/confirm_action"
```

Do not use a `pkill -f` pattern that mentions the fuzzel confirmation prompt in
the invoking command line. The `power_control.sh` script matches that pattern
against full command lines and kills the caller. Use `pkill -x fuzzel` to cancel
both menus.

Both modes use the same 752x498 frame, centered on each menu's bounding-box
center. The offsets come from a difference against the empty capture for that
mode, with the bar rows excluded:

```sh
for suffix in "" "-light"; do
  magick "meta/captures/menu-launcher${suffix}.png" -crop 752x498+581+307 +repage \
    -quality 92 "docs/images/picker-launcher${suffix}.webp"
  magick "meta/captures/menu-poweroff${suffix}.png" -crop 752x498+581+305 +repage \
    -quality 92 "docs/images/picker-poweroff${suffix}.webp"
done
```

If the menu changes size, recompute the frame:

```sh
magick meta/captures/menu-launcher.png meta/captures/empty-dark.png \
  -compose difference -composite -crop 1920x1040+0+40 +repage \
  -threshold 8% -trim info:
```

The output is the menu's bounding box in the cropped canvas. Add 40 pixels to
the y coordinate, center a 752x498 frame on the box, and use that frame's
offsets. Use `empty-light.png` when recomputing the light frames.

## Clipboard history

Capture the picker from a seeded database rather than the live one. The
`--db-path` flag points it at a throwaway file, so the real history stays
untouched and the capture holds no personal entries. Store the image last so it
lands at the newest id, which is the entry fzf selects on open and the one the
preview pane then shows:

```sh
D=/tmp/chezmoi-shots/cliphist-demo
mkdir -p "$D"
printf 'git rebase -i HEAD~3\n' | cliphist -db-path "$D/db" store
printf 'grep -rn "objects | select" home/ --include="*.sh"\n' | cliphist -db-path "$D/db" store
printf 'https://github.com/athaurian/dotfiles\n' | cliphist -db-path "$D/db" store
printf 'The palette lives in meta/palette.toml and every colour comes from it.\n' | cliphist -db-path "$D/db" store
magick docs/images/palette.webp -resize 800x png:- | cliphist -db-path "$D/db" store
```

The picker re-executes itself inside a titled `kitty` window, and that window
starts hidden in the scratchpad. The rule resizes and parks it, and the
`scratchpad show` below brings it back centered. Use an otherwise empty
workspace so nothing else lands in the capture:

```sh
~/.local/bin/palette-mode light
swaymsg workspace 5
dunstctl close-all
swaymsg exec "$HOME/.local/bin/clipboard --db-path $D/db"
sleep 2.5
swaymsg "[con_mark=clipboard_term] scratchpad show, resize set width 75 ppt height 70 ppt, move position center"
sleep 1
swaymsg '[con_mark=clipboard_term] focus'
sleep 2.5
dunstctl close-all
grim meta/captures/picker-clipboard.png
swaymsg -t get_tree | jq -r '[.. | objects | select(.name? == "clipboard_term")] | .[0] | "\(.rect.width)x\(.rect.height)@\(.rect.x),\(.rect.y)"' \
  > meta/captures/picker-clipboard.geom
```

Repeat in the other mode with `picker-clipboard-light.png` and the matching
`.geom` file. The recorded rectangle still includes the titlebar, so crop to the
picker's own border instead. Both modes draw that border in `srgb(95,95,95)`;
trimming the recorded rectangle to that colour gives `1410x665+9+19`:

```sh
magick meta/captures/picker-clipboard.png \
  -crop "$(cat meta/captures/picker-clipboard.geom)" +repage \
  -alpha off -fill black +opaque 'srgb(95,95,95)' \
  -fill white -opaque 'srgb(95,95,95)' -format '%@\n' info:
```

Add those offsets to the rectangle origin, which puts the frame at
`1410x665+255+230` for this window size. That keeps the rounded border, drops
the titlebar, and opts out of the corners that `extra.css` adds to figures:

```sh
for suffix in "" "-light"; do
  magick "meta/captures/picker-clipboard${suffix}.png" \
    -crop 1410x665+255+230 +repage \
    -quality 92 "docs/images/picker-clipboard${suffix}.webp"
done
```

Confirm the picker was focused before `grim`, since an unfocused picker dims its
preview pane and the capture comes out dimmed. Close the picker afterwards by
killing the window's process id, read from the same tree query. A
`swaymsg ... kill` on a kitty window leaves the process running, which prompts
for confirmation and keeps the window alive, and a `pkill -f` pattern that
matches the picker also matches the invoking shell and kills it:

```sh
P=$(swaymsg -t get_tree | jq -r '[.. | objects | select(.name? == "clipboard_term")] | .[0] | .pid')
kill "$P"
rm -rf "$D"
```

## Lock screen

The `lock.sh` script shows a 2.5-second warning, blurs a snapshot of the
desktop, then starts `swaylock`. The `grim` command captures the locked screen 8
seconds later. Unlock it yourself afterward. Pass literal `--timestr` and
`--datestr` values so the two captures show the same clock. The `lock.sh` script
forwards extra arguments to `swaylock`.

```sh
swaymsg workspace 3
dunstctl close-all
( sleep 8; grim meta/captures/lock-dark.png ) &
~/.config/sway/scripts/lock.sh --timestr '18:10' --datestr 'Mon, 19 Oct'
```

Wait 15 seconds at the password prompt before unlocking. For light mode, repeat
the capture with the same strings and save it as `lock-light.png`. Convert both
captures:

```sh
magick meta/captures/lock-dark.png -quality 92 docs/images/lock.webp
magick meta/captures/lock-light.png -quality 92 docs/images/lock-light.webp
```

Both published figures are re-encodes of the previous ones: the raws went to
`/tmp/chezmoi-shots/` under the earlier staging rule and were discarded, so the next
recapture has to start from a fresh raw.

## Status bar

Waybar occupies the top 24 pixels of the screen. Capture the strip on workspace
4 with the preview terminal focused, starting in light mode. Pause playback
first if the player is running, so the track does not change between modes:

```sh
playerctl pause
swaymsg workspace 4
swaymsg exec "kitty --class bar-preview --title hl_test.py nvim $HOME/.local/share/chezmoi/assets/hl_test.py"
sleep 2
swaymsg '[app_id=bar-preview] focus'
dunstctl close-all
grim -g "0,0 1920x24" meta/captures/bar-light.png
```

The `--title` flag fixes the focused window title, so the center module always
reads `hl_test.py`. Repeat with the `palette-mode dark` command and
`bar-dark.png`. The mode switch restarts Waybar and posts a notification, so
close notifications again before the second `grim`. Restore the session and
convert both strips:

```sh
~/.local/bin/palette-mode light
swaymsg '[app_id=bar-preview] kill'
swaymsg workspace 3
magick meta/captures/bar-dark.png -quality 92 docs/images/bar.webp
magick meta/captures/bar-light.png -quality 92 docs/images/bar-light.webp
```

Resume playback afterwards if it was running before the captures.

## Palette card

Render the palette card from the derived palette. It needs no session capture:

```sh
uv run --with pillow python3 meta/palette-card.py
```

## Themed images

The picker, lock, and status bar figures include both captures. The light URL
ends in `#only-light` and the dark URL in `#only-dark`. Zensical hides the
variant that does not match the active scheme. The GLightbox `auto_themed`
option in `zensical.toml` keeps the hidden variant out of the gallery.

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
