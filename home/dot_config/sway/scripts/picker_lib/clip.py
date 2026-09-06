"""Lists entries, decodes selections, and copies results via cliphist."""

from __future__ import annotations

import shutil
import subprocess

from picker_lib import model


class EntryNotFoundError(RuntimeError):
    """A cliphist entry vanished between listing and decoding it."""


def have_cliphist() -> bool:
    """Checks whether the cliphist binary is available."""
    return shutil.which("cliphist") is not None


def _base_args(db_path: str | None) -> list[str]:
    args = ["cliphist"]
    if db_path is not None:
        args += ["-db-path", db_path]
    return args


def list_entries(db_path: str | None = None) -> list[tuple[int, str]]:
    """Lists clipboard history as id and display pairs, newest first.

    Malformed lines are skipped. Raises FileNotFoundError when cliphist
    is missing and RuntimeError when listing fails.
    """
    try:
        result = subprocess.run(
            _base_args(db_path) + ["list"],
            check=False,
            capture_output=True,
            text=True,
            # Previews may carry arbitrary bytes. Skip one bad entry
            # instead of failing the whole listing. Ids are ASCII and survive.
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError("cliphist not installed") from exc
    if result.returncode != 0:
        # No database file yet means nothing was stored, which is an
        # empty history rather than an error. This is cliphist's own
        # wording, so it stays coupled to it. Anything else still raises.
        if "please store something first" in result.stderr:
            return []
        raise RuntimeError(f"cliphist list failed: {result.stderr.strip()}")
    entries = []
    for line in result.stdout.splitlines():
        eid, display = model.split_entry(line)
        if eid is None:
            continue
        entries.append((eid, display))
    return entries


def decode(payload: bytes, db_path: str | None = None) -> bytes:
    """Decodes a cliphist selection from a full menu line or bare id to raw bytes.

    The payload must not end with a newline. Cliphist rejects bare ids
    with a trailing newline, so callers pass exact bytes.
    """
    try:
        result = subprocess.run(
            _base_args(db_path) + ["decode"],
            input=payload,
            check=False,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError("cliphist not installed") from exc
    if result.returncode != 0:
        err = result.stderr.decode()
        # The entry expired (history rotated) after listing. Cliphist
        # reports this as "id N not found", which callers translate to
        # a friendly message instead of a raw failure.
        if "not found" in err:
            raise EntryNotFoundError(err.strip())
        raise RuntimeError(f"cliphist decode failed: {err!r}")
    return result.stdout


def copy_to_clipboard(data: bytes) -> None:
    """Copies raw bytes to the Wayland clipboard with MIME type auto-detected.

    Raises FileNotFoundError when wl-copy is missing and RuntimeError
    when copying fails.
    """
    try:
        # Do not capture the output from wl-copy. It forks a background
        # daemon to serve the clipboard, which inherits the pipes and
        # holds them open, so communicate() waits for EOF forever even
        # though the copy succeeds.
        result = subprocess.run(
            ["wl-copy"],
            input=data,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError("wl-copy not installed") from exc
    if result.returncode != 0:
        raise RuntimeError(f"wl-copy failed with status {result.returncode}")
