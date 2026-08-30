"""Manager-owned Neovim session snapshots and Snacks sidecar files."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import MANAGER_SESSIONOPTIONS, STATE_DIR, escape_cwd
from .rpc import nvim_rpc
from .swap import cleanup_stale_swapfiles

log = logging.getLogger("session_manager")


def get_nvim_snapshot_path(cwd: str, pid: int | None = None) -> Path:
    escaped = escape_cwd(cwd)
    if pid is not None:
        escaped = f"{escaped}%{pid}"
    return STATE_DIR / "nvim" / "manager" / f"{escaped}.vim"


def snacks_sidecar_path(snapshot_path: Path) -> Path:
    return Path(str(snapshot_path) + ".snacks")


def create_manager_snapshot(
    server_path: str,
    snapshot_path: Path,
    nvim_pid: int | None,
) -> tuple[bool, str | None]:
    lua = f"""
(function()
  local out = {{}}
  local target = {json.dumps(str(snapshot_path))}
  local snacks_target = target .. ".snacks"

  local old_sessionoptions = vim.o.sessionoptions
  local old_this_session = vim.v.this_session

  vim.o.sessionoptions = {json.dumps(MANAGER_SESSIONOPTIONS)}

  local snacks_f = io.open(snacks_target, "w")
  local snacks_explorer_open = 0
  if snacks_f then
    local pok, pickers = pcall(function()
      return Snacks.picker.get({{ source = "explorer" }})
    end)
    if pok and type(pickers) == "table" and #pickers > 0 then
      snacks_explorer_open = 1
    end
    snacks_f:write(tostring(snacks_explorer_open))
    snacks_f:close()
  end

  local ok, err = pcall(
    vim.cmd,
    "silent mksession! " .. vim.fn.fnameescape(target)
  )
  out.snapshot_ok = ok
  out.snapshot_error = ok and "" or tostring(err)

  vim.o.sessionoptions = old_sessionoptions
  pcall(function() vim.v.this_session = old_this_session end)

  out.snacks_explorer_open = snacks_explorer_open
  return out
end)()
""".strip()
    result = nvim_rpc(server_path, lua, "snapshot_ok")
    if result is None:
        return False, "RPC failed"

    if not result.get("snapshot_ok"):
        return False, result.get("snapshot_error", "unknown")

    if not snapshot_path.exists():
        return False, "Snapshot file missing after mksession"

    try:
        snapshot_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, f"Unreadable snapshot: {exc}"

    removed = cleanup_stale_swapfiles(snapshot_path)
    if removed > 0:
        log.info(
            "Cleaned up %d stale swapfile(s) from snapshot %s", removed, snapshot_path
        )

    log.info(
        "Snapshot created: %s  (Snacks explorer: %s, stale swaps removed: %d)",
        snapshot_path,
        "open" if result.get("snacks_explorer_open") else "closed",
        removed,
    )
    return True, None
