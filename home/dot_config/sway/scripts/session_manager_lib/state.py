"""Mutable restore context threaded through the restore call chain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RestoreContext:
    """Mutable state for a single restore run."""

    claimed_ids: set[int] = field(default_factory=set)
    current_workspace: str | None = None

    # Helium group restore state
    helium_saved_nodes: list[dict] = field(default_factory=list)
    helium_saved_index: dict[int, int] = field(default_factory=dict)
    helium_restored_ids: list[int | None] = field(default_factory=list)
    helium_restore_started: bool = False
