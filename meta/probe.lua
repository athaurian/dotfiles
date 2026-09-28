-- Core semantics probe: One Dark on Neutral, locked (meta/color-scheme.md).
-- Run headless from anywhere; self-quits (exit 1 on any FAIL):
--   nvim --headless -c "luafile <repo>/meta/probe.lua"
-- Headless-only: refuses to run with a UI attached (never :q! a live session).
--
-- Expectations come from home/.chezmoidata.yaml, the generator's output for
-- the machine's active mode, so the probe follows palette and mode changes
-- without edits. The loaded colorscheme follows the mode too: catppuccin-latte
-- on light, catppuccin-mocha on dark.
--
-- Contract: this verifies the DEPLOYED config (~/.config/nvim) against the
-- source palette data, so run it after `chezmoi apply`. A stale deployment is
-- detected and reported instead of producing a wall of mismatches.

if #vim.api.nvim_list_uis() > 0 then
  io.stderr:write("probe: refusing to run with a UI attached (headless only)\n")
  vim.cmd("cquit 2")
end

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
for key, hex in data_text:gmatch("%s*([%w_]+): { hex: \"(#%x%x%x%x%x%x)\"") do
  p[key] = hex
end

local expected = mode == "light" and "latte" or "mocha"
local deployed = io.open(vim.env.HOME .. "/.config/nvim/lua/plugins/colorscheme.lua", "r")
if not deployed then
  io.stderr:write("probe: deployed colorscheme.lua missing; run chezmoi apply\n")
  vim.cmd("cquit 2")
end
local deployed_text = deployed:read("*a")
deployed:close()
if not deployed_text:find('colorscheme = "catppuccin-' .. expected .. '"', 1, true) then
  io.stderr:write("probe: deployed nvim does not match mode " .. mode
    .. " (expected catppuccin-" .. expected .. "); run chezmoi apply\n")
  vim.cmd("cquit 2")
end

pcall(vim.cmd, "colorscheme catppuccin-" .. expected)

local failures = 0
local function hex(n)
  return n and string.format("#%06X", n) or nil
end
local function check(group, attr, want)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  local got = ok and hl and hex(hl[attr]) or nil
  if got == want then
    print(string.format("PASS %-24s %s=%s", group, attr, want))
  else
    failures = failures + 1
    print(string.format("FAIL %-24s %s: want %s got %s", group, attr, want, tostring(got)))
  end
end
local function check_flag(group, flag)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  if ok and hl and hl[flag] then
    print(string.format("PASS %-24s %s", group, flag))
  else
    failures = failures + 1
    print(string.format("FAIL %-24s %s: not set", group, flag))
  end
end
local function check_nobg(group)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = group, link = false })
  if ok and hl and hl.bg == nil then
    print(string.format("PASS %-24s bg=none", group))
  else
    failures = failures + 1
    print(string.format("FAIL %-24s bg: want none got %s", group, tostring(hl and hl.bg)))
  end
end
local function check_gvar(name, want)
  local got = vim.g[name]
  if got == want then
    print(string.format("PASS %-24s =%s", name, want))
  else
    failures = failures + 1
    print(string.format("FAIL %-24s : want %s got %s", name, want, tostring(got)))
  end
end

-- Grounds and semantics (meta/color-scheme.md).
check("Normal", "fg", p.text)
check("Comment", "fg", p.muted)
check_flag("Comment", "italic")
check("@comment", "fg", p.muted)
check("@property", "fg", p.orange)
check("@variable.parameter", "fg", p.text)
check("@string.escape", "fg", p.cyan)
check("@tag", "fg", p.red)

-- Cursor, selection, search. Cursors carry on-accent text over the accent.
check("Cursor", "bg", p.blue)
check("Cursor", "fg", p.on_accent)
check("TermCursor", "bg", p.blue)
check("Visual", "bg", p.selection)
check("CurSearch", "bg", p.selection)
check("CurSearch", "fg", p.text_max)

-- Live integrations: palette blue intact through overrides.
check("DiagnosticInfo", "fg", p.blue)
check("WhichKeyDesc", "fg", p.text)
check("NoiceCmdlineIcon", "fg", p.blue)
check("DiffAdd", "bg", p.diff_add)
check("DiffText", "bg", p.diff_text)

-- Audit pins: markdown heading grounds neutral, chrome borders on surface-2
-- (btop's box grey).
check("RenderMarkdownH1Bg", "bg", p.surface_0)
check("BlinkCmpMenuBorder", "fg", p.surface_2)
check("WinSeparator", "fg", p.surface_2)
check("FloatBorder", "fg", p.surface_2)

-- Snacks terminal stays transparent like the editor.
check_nobg("SnacksNormal")
check_nobg("SnacksNormalNC")

-- Terminal ANSI (red/cursor codes).
check_gvar("terminal_color_0", p.base)
check_gvar("terminal_color_1", p.red)
check_gvar("terminal_color_4", p.blue)
check_gvar("terminal_color_9", p.red_bright)

if failures > 0 then
  print(string.format("probe: %d FAILURES", failures))
  vim.cmd("cquit 1")
end
print("probe: all green (" .. mode .. ")")
vim.cmd("qa!")
