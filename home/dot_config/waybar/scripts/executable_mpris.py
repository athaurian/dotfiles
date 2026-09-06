#!/usr/bin/env python3
"""
Waybar MPRIS module script.

The script uses a hybrid of event handling and polling. The `playerctl --follow`
stream provides instant, event-driven updates. A periodic resync every
`POLL_INTERVAL` seconds queries authoritative state and corrects whatever the
follow stream misses or gets wrong.

The script emits Waybar-compatible JSON to stdout. An empty payload when
no player is active lets Waybar's `hide-empty-text` collapse the module
cleanly.

The two approaches cover for each other. Polling alone is reliable but
slow, adding up to one second of latency to every play, pause, or track
change. The `--follow` stream alone reacts instantly, but it misses or
coalesces rapid `PropertiesChanged` bursts, stops emitting when a browser's
MPRIS instance churns, and passes through Chromium-family quirks. Running
both through one state machine gives instant updates with self-healing.

Three safety nets compensate for those browser quirks:

- The last-known-good cache keeps showing the previous artist and title
  while a player is Playing or Paused but its metadata is momentarily
  empty. Chromium clears `Metadata` during long pauses and track changes.
- Position-stall pause detection handles the case where Chromium reports
  `PlaybackStatus` "Playing" while actually paused. A frozen non-zero
  `{{position}}` across consecutive readings renders as Paused.
- The grace window keeps the cached song visible through Chromium's brief
  empty or Stopped state during track transitions.

The script emits only actual state changes, so Waybar is not re-rendered
on every event.
"""

import html
import json
import os
import queue
import subprocess
import sys
import threading
import time
import unicodedata
from functools import lru_cache

ICON_PLAYING = "󰐊"
ICON_PAUSED = "󰏤"

MAX_TEXT_LEN = 56

# Interval between authoritative resync queries. Override it with the
# `MPRIS_POLL_INTERVAL` environment variable so the test harness can run
# scenarios quickly without waiting one second per poll.
POLL_INTERVAL = float(os.environ.get("MPRIS_POLL_INTERVAL", "1.0"))

# Chromium keeps `PlaybackStatus` "Playing" while paused. A frozen non-zero
# position is the only reliable signal. A position counts as frozen only
# once it has stayed identical for `STALL_MIN_TIME`, which ignores
# near-simultaneous duplicate readings, for example a follow event echoed
# by the resync poll milliseconds later. `STALL_POLLS` is the number of
# qualifying consecutive readings required before downgrading to Paused.
STALL_DETECTION = True
STALL_MIN_TIME = float(os.environ.get("MPRIS_STALL_MIN_TIME", "1.0"))
STALL_POLLS = int(os.environ.get("MPRIS_STALL_POLLS", "1"))

# During track transitions Chromium briefly reports an empty or Stopped
# state. Here that shows up as a window of roughly 0.3 to 0.5 seconds of
# empty reads between tracks, and follow mode can deliver many such
# readings in a burst. Stopped readings are masked for this long after the
# last genuinely active reading, so the cached song stays visible through
# the gap at any event cadence. A genuine stop clears after the window
# elapses.
GRACE_SECONDS = float(os.environ.get("MPRIS_GRACE_SECONDS", "2.0"))

_EMPTY_PAYLOAD: str = json.dumps({"text": "", "class": "stopped", "alt": "stopped"})
_SPAN_PLAYING: str = f"<span>{ICON_PLAYING}</span>"
_SPAN_PAUSED: str = f"<span>{ICON_PAUSED}</span>"

# Unit separator between playerctl format fields. Real titles never contain
# it, unlike tabs.
_FIELD_SEP = "\x1f"


@lru_cache(maxsize=2048)
def _char_width(ch: str) -> int:
    """Returns the terminal column width of a single character."""
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1


def _truncate(label: str, limit: int = MAX_TEXT_LEN) -> str:
    """
    Truncates the label to fit within `limit` display columns and appends
    an ellipsis when truncation occurs.

    Uses per-character display width rather than code point count so CJK
    and wide emoji are handled correctly. Character widths are cached
    through `lru_cache` to amortize the `unicodedata` lookup cost across
    repeated calls.
    """
    width = 0
    for i, ch in enumerate(label):
        width += _char_width(ch)
        if width > limit:
            return label[:i] + "…"
    return label


def _emit(payload: str) -> None:
    """Writes a single Waybar JSON line to stdout and flushes immediately."""
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()


def _parse_position(pos: str) -> int | None:
    """Parses the playerctl position string and returns None when the position is missing or non-positive."""
    try:
        value = int(pos.strip())
    except (AttributeError, ValueError):
        return None
    return value if value > 0 else None


def _playerctl_cmd(follow: bool) -> list[str]:
    """Builds the playerctl metadata command, with or without `--follow`."""
    cmd = ["playerctl", "--player=%any", "metadata"]
    if follow:
        cmd.append("--follow")
    cmd.extend(
        [
            "--format",
            _FIELD_SEP.join(
                (
                    "{{playerName}}",
                    "{{status}}",
                    "{{position}}",
                    "{{artist}}",
                    "{{title}}",
                )
            ),
        ]
    )
    return cmd


def _split_fields(line: str) -> tuple[str, str, str, str, str] | None:
    """Parses one playerctl output line into `(player, status, position, artist, title)`."""
    line = line.strip()
    if not line:
        return None
    fields = line.split(_FIELD_SEP, 4)
    player = fields[0].strip() if len(fields) > 0 else ""
    status = fields[1].strip() if len(fields) > 1 else ""
    position = fields[2].strip() if len(fields) > 2 else ""
    artist = fields[3].strip() if len(fields) > 3 else ""
    title = fields[4].strip() if len(fields) > 4 else ""
    return player, status, position, artist, title


def _query_player() -> tuple[str, str, str, str, str] | None:
    """
    Runs playerctl once for an authoritative snapshot.

    Returns the field tuple on success, `("", "", "", "", "")` when no
    player is active, or None when the query failed transiently. A
    transient failure skips the reading without emitting a state change.
    """
    try:
        proc = subprocess.run(
            _playerctl_cmd(follow=False),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        _emit(_EMPTY_PAYLOAD)
        sys.exit(0)
    except subprocess.TimeoutExpired:
        return None

    if proc.returncode != 0 or not proc.stdout.strip():
        return "", "", "", "", ""
    return _split_fields(proc.stdout)


def _render(status: str, artist: str, title: str) -> str:
    """
    Builds the Waybar JSON payload for an active player.

    Formats the label as `Artist - Title` and falls back to just the title
    or artist when only one field is present. Applies italic Pango markup
    when paused. Returns the empty payload when both fields are absent,
    which can happen briefly during player startup before metadata
    arrives.
    """
    span = _SPAN_PLAYING if status == "Playing" else _SPAN_PAUSED

    if artist and title:
        label = f"{artist} - {title}"
    elif title:
        label = title
    elif artist:
        label = artist
    else:
        return _EMPTY_PAYLOAD

    label = _truncate(label)
    # Waybar parses Pango markup. Escape is false in the module config,
    # so escape track metadata that could contain ``&``, ``<``, or ``>``.
    label = html.escape(label, quote=False)
    text = f"{span}  {label}"

    if status == "Paused":
        text = f"<i>{text}</i>"

    return json.dumps({"text": text, "class": status.lower(), "alt": status.lower()})


class _PlayerState:
    """
    Renders playerctl readings from follow events and resync polls alike
    into Waybar payloads. Maintains the last-known-good cache, the
    position-stall heuristic, and the Stopped grace window.
    """

    def __init__(self) -> None:
        self.cache_artist = ""
        self.cache_title = ""
        self.last_status = ""
        self.last_player = ""
        self.last_pos: int | None = None
        self.last_pos_time: float | None = None
        self.last_active_time: float | None = None
        self.stall = 0
        self.last_payload = _EMPTY_PAYLOAD

    def process(self, fields: tuple[str, str, str, str, str] | None) -> str | None:
        """
        Feeds one reading into the state machine.

        Returns the payload to emit, or None when the rendered state is
        unchanged. This covers deduplication and grace-masked transitions.
        """
        if fields is None:
            return None

        player, status, position, artist, title = fields
        payload = _EMPTY_PAYLOAD

        if status == "Stopped" or not status:
            now = time.monotonic()
            still_grace = (
                self.last_active_time is not None
                and now - self.last_active_time < GRACE_SECONDS
            )
            if still_grace and (self.cache_artist or self.cache_title):
                # Transient gap, for example Chromium mid track-change. Keep
                # the last known good visible instead of blinking blank.
                payload = _render(self.last_status, self.cache_artist, self.cache_title)
            else:
                self.cache_artist = self.cache_title = ""
                self.last_status = ""
                self.last_player = ""
                self.last_pos = None
                self.last_pos_time = None
                self.last_active_time = None
                self.stall = 0
        else:
            self.last_active_time = time.monotonic()

            if player != self.last_player:
                # New player, for example a different Chromium tab
                # instance. Never carry another player's metadata forward.
                self.last_player = player
                self.cache_artist = self.cache_title = ""
                self.last_pos = None
                self.last_pos_time = None
                self.stall = 0

            if artist and title:
                self.cache_artist, self.cache_title = artist, title
            else:
                # Player is reporting empty metadata while active, for
                # example Chromium clears Metadata during long pauses and
                # track transitions. Fall back to the last known good.
                artist = artist or self.cache_artist
                title = title or self.cache_title

            if STALL_DETECTION and status == "Playing":
                pos = _parse_position(position)
                now = time.monotonic()
                if pos is not None:
                    if pos == self.last_pos and self.last_pos_time is not None:
                        # Same position as the previous reading. It counts
                        # as frozen only once it has persisted for
                        # STALL_MIN_TIME, ignoring duplicate readings
                        # milliseconds apart.
                        if now - self.last_pos_time >= STALL_MIN_TIME:
                            self.stall += 1
                            if self.stall >= STALL_POLLS:
                                status = "Paused"
                    else:
                        self.stall = 0
                        self.last_pos = pos
                        self.last_pos_time = now
                else:
                    self.stall = 0
                    self.last_pos = None
                    self.last_pos_time = None
            else:
                self.stall = 0
                self.last_pos = None
                self.last_pos_time = None

            self.last_status = status
            payload = _render(status, artist, title)

        if payload == self.last_payload:
            return None
        self.last_payload = payload
        return payload


def _follow_reader(proc: subprocess.Popen, events: queue.Queue) -> None:
    """
    Drains the follow stream into a queue on a background thread.

    A dedicated reader avoids the `select` pitfall with a buffered pipe,
    where bursty follow lines linger in the Python-side buffer while
    `select` receives nothing at the OS level. That delays or drops events.
    """
    for line in proc.stdout:
        events.put(("line", line))
    events.put(("eof", None))


def main() -> None:
    """
    Streams follow events and periodically resyncs authoritative state.

    Follow events are handled the moment they arrive, which gives an
    instant play and pause response. The queue timeout triggers an
    authoritative one-shot query that corrects anything the follow stream
    missed. A dead follow process is respawned, and the resync keeps state
    honest while it is down. Emits an empty payload on startup and when
    the player is genuinely Stopped or gone.
    """
    state = _PlayerState()
    proc: subprocess.Popen | None = None
    events: queue.Queue = queue.Queue()

    _emit(_EMPTY_PAYLOAD)

    while True:
        if proc is None:
            try:
                proc = subprocess.Popen(
                    _playerctl_cmd(follow=True),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            except FileNotFoundError:
                _emit(_EMPTY_PAYLOAD)
                sys.exit(0)
            threading.Thread(
                target=_follow_reader, args=(proc, events), daemon=True
            ).start()
            continue

        try:
            kind, value = events.get(timeout=POLL_INTERVAL)
        except queue.Empty:
            # Follow was silent. Re-query authoritative state and correct
            # anything the event stream missed or got wrong.
            payload = state.process(_query_player())
            if payload is not None:
                _emit(payload)
            continue

        if kind == "eof":
            # Follow died, for example because no players are registered
            # or the player closed. Respawn on the next iteration. The
            # resync on the next timeout keeps state honest meanwhile.
            # Reap the child so it does not linger as a zombie.
            if proc is not None:
                try:
                    proc.wait(timeout=2.0)
                except (OSError, subprocess.SubprocessError):
                    pass
            proc = None
            continue

        payload = state.process(_split_fields(value))
        if payload is not None:
            _emit(payload)


if __name__ == "__main__":
    main()
