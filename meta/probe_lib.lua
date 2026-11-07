-- Shared setup for the palette probes that run headless.
--
-- The palette data is gitignored, so a new clone runs `make palette` first.
-- The deployed Neovim config must have the same mode as the data. The
-- assertions read the colorscheme that LazyVim loads.
local lib = {}

function lib.headless(name)
  if #vim.api.nvim_list_uis() > 0 then
    io.stderr:write(name .. ": refusing to run with a UI attached (headless only)\n")
    vim.cmd("cquit 2")
  end
end

function lib.load()
  local script_path = debug.getinfo(1, "S").source:sub(2)
  local repo_root = vim.fs.dirname(vim.fs.dirname(script_path))
  local data_path = repo_root .. "/home/.chezmoidata.yaml"

  local data_file = io.open(data_path, "r")
  if not data_file then
    io.stderr:write("probe: missing " .. data_path .. "; run make palette\n")
    vim.cmd("cquit 2")
  end
  local data_text = data_file:read("*a")
  data_file:close()

  local mode = nil
  for line in data_text:gmatch("[^\n]+") do
    mode = line:match("^mode:%s*(%S+)")
    if mode then break end
  end
  if not mode then
    io.stderr:write("probe: no mode token in " .. data_path .. "\n")
    vim.cmd("cquit 2")
  end

  local p = {}
  for key, hex in data_text:gmatch('%s*([%w_]+): { hex: "(#%x%x%x%x%x%x)"') do
    p[key] = hex
  end

  local flavour = mode == "light" and "latte" or "mocha"
  local deployed = io.open(vim.env.HOME .. "/.config/nvim/lua/plugins/colorscheme.lua", "r")
  if not deployed then
    io.stderr:write("probe: deployed colorscheme.lua missing; run chezmoi apply\n")
    vim.cmd("cquit 2")
  end
  local deployed_text = deployed:read("*a")
  deployed:close()
  if not deployed_text:find('colorscheme = "catppuccin-' .. flavour .. '"', 1, true) then
    io.stderr:write("probe: deployed nvim does not match mode " .. mode
      .. " (expected catppuccin-" .. flavour .. "); run chezmoi apply\n")
    vim.cmd("cquit 2")
  end

  lib.mode = mode
  lib.flavour = flavour
  lib.p = p
  lib.failures = 0
  pcall(vim.cmd, "colorscheme catppuccin-" .. flavour)
  return lib
end

function lib.hex(value)
  return value and string.format("#%06X", value) or nil
end

function lib.pass(message)
  print("PASS " .. message)
end

function lib.fail(message)
  lib.failures = lib.failures + 1
  print("FAIL " .. message)
end

function lib.check(group, attr, want)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  local got = ok and hl and lib.hex(hl[attr]) or nil
  if got == want then
    print(string.format("PASS %-24s %s=%s", group, attr, want))
  else
    lib.failures = lib.failures + 1
    print(string.format("FAIL %-24s %s: want %s got %s", group, attr, want, tostring(got)))
  end
end

function lib.check_flag(group, flag)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  if ok and hl and hl[flag] then
    print(string.format("PASS %-24s %s", group, flag))
  else
    lib.failures = lib.failures + 1
    print(string.format("FAIL %-24s %s: not set", group, flag))
  end
end

function lib.check_nobg(group)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  if ok and hl and hl.bg == nil then
    print(string.format("PASS %-24s bg=none", group))
  else
    lib.failures = lib.failures + 1
    print(string.format("FAIL %-24s bg: want none got %s", group, tostring(hl and hl.bg)))
  end
end

function lib.check_gvar(name, want)
  local got = vim.g[name]
  if got == want then
    print(string.format("PASS %-24s =%s", name, want))
  else
    lib.failures = lib.failures + 1
    print(string.format("FAIL %-24s : want %s got %s", name, want, tostring(got)))
  end
end

function lib.report(name)
  if lib.failures > 0 then
    print(string.format("%s: %d FAILURES", name, lib.failures))
    vim.cmd("cquit 1")
  end
  print(name .. ": all green (" .. lib.mode .. ")")
  vim.cmd("qa!")
end

return lib
