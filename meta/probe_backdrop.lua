if #vim.api.nvim_list_uis() > 0 then
  io.stderr:write("probe_backdrop: refusing to run with a UI attached (headless only)\n")
  vim.cmd("cquit 2")
end
pcall(vim.cmd, "colorscheme catppuccin-mocha")

local failures = 0
local function pass(msg)
  print("PASS " .. msg)
end
local function fail(msg)
  failures = failures + 1
  print("FAIL " .. msg)
end

local ok, dim = pcall(vim.api.nvim_get_hl, 0, { name = "BackdropDim", link = false })
if ok and dim and dim.bg == 0x000000 then
  pass("BackdropDim bg=#000000")
else
  fail("BackdropDim bg: want #000000")
end

local nok, normal = pcall(vim.api.nvim_get_hl, 0, { name = "Normal", link = false })
if nok and normal and normal.bg == nil then
  pass("Normal bg=none (plugin dims skipped, autocmds take over)")
else
  fail("Normal bg: want none")
end

local cok, cat = pcall(require, "catppuccin")
if cok and cat.options and cat.options.transparent_background == true then
  pass("transparent_background=true")
else
  fail("transparent_background: want true")
end

local function patterns(event)
  local go, aus = pcall(vim.api.nvim_get_autocmds, { group = "backdrop-dim", event = event })
  if not go then
    return nil
  end
  local pats = {}
  for _, au in ipairs(aus) do
    pats[type(au.pattern) == "table" and table.concat(au.pattern, ",") or au.pattern] = true
  end
  return pats
end
local ft = patterns("FileType")
if ft and ft.mason and ft.lazy then
  pass("FileType mason+lazy registered")
else
  fail("FileType mason+lazy: not both registered")
end
if patterns("WinClosed") then
  pass("WinClosed cleanup registered")
else
  fail("WinClosed cleanup: missing")
end
if patterns("VimResized") then
  pass("VimResized re-fit registered")
else
  fail("VimResized re-fit: missing")
end

if failures > 0 then
  print(string.format("probe_backdrop: %d FAILURES", failures))
  vim.cmd("cquit 1")
end
print("probe_backdrop: all green")
vim.cmd("qa!")
