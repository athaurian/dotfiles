"""Live Neovim instance inspection via RPC."""

from __future__ import annotations

from pathlib import Path

from ..proc_cache import ProcCache
from .rpc import nvim_rpc
from .sockets import runtime_nvim_sockets, sock_pid


def inspect_nvim_socket(socket_path: Path) -> tuple[int | None, dict | None]:
    server_pid = sock_pid(socket_path)

    lua_inspect = r"""
(function()
  local out = {
    pid = vim.fn.getpid(),
    cwd = vim.fn.getcwd(),
    argc = vim.fn.argc(),
    this_session = vim.v.this_session,
    errmsg = vim.v.errmsg,
    buffers = {},
    windows = {},
  }
  local snacks_explorer_open = 0
  local pok, pickers = pcall(function()
    return Snacks.picker.get({ source = "explorer" })
  end)
  if pok and type(pickers) == "table" and #pickers > 0 then
    snacks_explorer_open = 1
  end
  out.snacks_explorer_open = snacks_explorer_open

  for _, buffer in ipairs(vim.api.nvim_list_bufs()) do
    local function option(name)
      local ok, value = pcall(vim.api.nvim_get_option_value, name, { buf = buffer })
      return ok and value or "<error>"
    end
    table.insert(out.buffers, {
      id = buffer,
      name = vim.api.nvim_buf_get_name(buffer),
      loaded = vim.api.nvim_buf_is_loaded(buffer),
      listed = vim.fn.buflisted(buffer) == 1,
      buftype = option("buftype"),
      filetype = option("filetype"),
      modified = option("modified"),
      window_count = #vim.fn.win_findbuf(buffer),
    })
  end
  for _, win in ipairs(vim.api.nvim_list_wins()) do
    local buffer = vim.api.nvim_win_get_buf(win)
    table.insert(out.windows, {
      win = win, buffer = buffer,
      name = vim.api.nvim_buf_get_name(buffer),
      buftype = vim.api.nvim_get_option_value("buftype", { buf = buffer }),
      filetype = vim.api.nvim_get_option_value("filetype", { buf = buffer }),
    })
  end
  return out
end)()
""".strip()

    result = nvim_rpc(str(socket_path), lua_inspect, "pid")
    if result is not None:
        server_pid = result.get("pid")
    return server_pid, result


def get_foot_nvim_state(
    pid: int, cache: ProcCache | None = None
) -> tuple[int | None, dict | None]:
    cache = cache or ProcCache.snapshot()
    nvim_pid = cache.get_nvim_pid(pid)
    if nvim_pid is None:
        return None, None

    sock_pid_map: dict[int, Path] = {}
    for s in runtime_nvim_sockets():
        spid = sock_pid(s)
        if spid is not None:
            sock_pid_map[spid] = s

    if nvim_pid in sock_pid_map:
        _, state = inspect_nvim_socket(sock_pid_map[nvim_pid])
        return nvim_pid, state

    for candidate_pid in cache.descendants(pid):
        if candidate_pid == nvim_pid:
            continue
        if candidate_pid in sock_pid_map:
            _, state = inspect_nvim_socket(sock_pid_map[candidate_pid])
            return candidate_pid, state

    return nvim_pid, None


def is_dashboard_state(state: dict) -> bool:
    named_normal = [
        b["name"]
        for b in state.get("buffers", [])
        if b.get("buftype") == "" and bool(b.get("name"))
    ]
    return len(named_normal) == 0
