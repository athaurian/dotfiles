# Screenshot capture

The images in `docs/images/` come from a live Sway session, and the automatic
ones are produced by a single script. Because the script stages windows on a
fixed workspace and switches the palette mode, it must run in an otherwise idle
session.

**Precondition.** Workspace 3 must be empty because the script stages windows
there.

Run this command from the repository root:

```sh
make shots
```

| Phase  | Behavior                                                            |
| :----- | :------------------------------------------------------------------ |
| Setup  | Moves to workspace 3                                                |
| Output | Writes the automatic captures and composed images to `docs/images/` |
| Kept   | Raw captures in `meta/captures/`; `.geom` files left in place       |
| Exit   | Restores the original palette mode and workspace                    |

The script takes over workspace 3 for the run, keeps raw captures in
`meta/captures/`, and leaves the `.geom` files in place. You can run one script
for a single figure under `meta/shots/`. The automatic entry point is
`meta/shots/redo-all.sh`. Run that script with `--help` to list its actions.

## Lock screen

A lock-screen capture requires a locked session and a real unlock. It is not
part of the automatic script. Capture one image per mode:

```sh
meta/shots/lock.py dark
meta/shots/lock.py light
```

Wait at least 15 seconds after starting a capture before you unlock the screen.

| Parameter            | Value                                              |
| :------------------- | :------------------------------------------------- |
| Delay before capture | 8 seconds, for the lock screen and clock to render |
| Minimum time locked  | 15 seconds after starting a capture                |

## Discord captures

Discord must be signed in before taking these captures. Save a full-screen
capture for each mode as these files:

- `meta/captures/discord-dark.png`
- `meta/captures/discord-light.png`

Then compose both files with:

```sh
meta/shots/discord.py compose
```
