local here = vim.fs.dirname(debug.getinfo(1, "S").source:sub(2))
package.path = here .. "/?.lua;" .. package.path
local probe = require("probe_lib")

probe.headless("probe_backdrop")
probe.load()
local p = probe.p

local black = tonumber(p.black:sub(2), 16)

local ok, dim = pcall(vim.api.nvim_get_hl, 0, { name = "BackdropDim", link = false })
if ok and dim and dim.bg == black then
  probe.pass("BackdropDim bg=" .. p.black)
else
  probe.fail("BackdropDim bg: want " .. p.black)
end

local nok, normal = pcall(vim.api.nvim_get_hl, 0, { name = "Normal", link = false })
if nok and normal and normal.bg == nil then
  probe.pass("Normal bg=none (plugin dims skipped, autocmds take over)")
else
  probe.fail("Normal bg: want none")
end

local cok, cat = pcall(require, "catppuccin")
if cok and cat.options and cat.options.transparent_background == true then
  probe.pass("transparent_background=true")
else
  probe.fail("transparent_background: want true")
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
  probe.pass("FileType mason+lazy registered")
else
  probe.fail("FileType mason+lazy: not both registered")
end
if patterns("WinClosed") then
  probe.pass("WinClosed cleanup registered")
else
  probe.fail("WinClosed cleanup: missing")
end
if patterns("VimResized") then
  probe.pass("VimResized re-fit registered")
else
  probe.fail("VimResized re-fit: missing")
end

probe.report("probe_backdrop")
