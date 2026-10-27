# Screenshot capture

The images in `docs/images/` come from a live Sway session. The script
`meta/shots/redo-all.sh` makes every capture that does not need manual work.

Run this command from the repository root:

```sh
meta/shots/redo-all.sh
```

The script takes over workspace 3 and makes the automatic captures and the
composed images. It keeps the raw captures in `meta/captures/` and leaves the
`.geom` files in place. At the end it sets dark mode again and returns to
workspace 1.

You can run one script for a single figure. Run the script with `--help` to see
its actions.

The lock and Discord captures are not in the automatic script because they need
manual work.

## Lock screen

Run one command for each mode:

```sh
meta/shots/lock.py dark
meta/shots/lock.py light
```

Wait at least 15 seconds after starting a capture before you unlock the screen.

## Discord captures

Save a full screen capture for each mode as these files:

- `meta/captures/discord-dark.png`
- `meta/captures/discord-light.png`

Then crop both files with this command:

```sh
meta/shots/discord.py compose
```
