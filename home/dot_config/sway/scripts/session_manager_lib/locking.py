"""Interprocess lock for save/restore operations."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .config import LOCK_FILE_NAME


@contextmanager
def operation_lock(state_dir: Path) -> Iterator[None]:
    """Serialize session-manager operations across processes."""
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / LOCK_FILE_NAME
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
