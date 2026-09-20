-- Core semantics probe: One Dark on Neutral, locked (meta/color-scheme.md).
-- Run headless from the repo root; self-quits (exit 1 on any FAIL):
--   nvim --headless -c "luafile <repo>/meta/probe.lua"
-- Headless-only: refuses to run with a UI attached (never :q! a live session).

if #vim.api.nvim_list_uis() > 0 then
  io.stderr:write("probe: refusing to run with a UI attached (headless only)\n")
  vim.cmd("cquit 2")
end
pcall(vim.cmd, "colorscheme catppuccin-mocha")

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

-- Grounds and semantics (rules 2-3).
check("Normal", "fg", "#D4D4D4")
check("Comment", "fg", "#8A8A8A")
check_flag("Comment", "italic")
check("@comment", "fg", "#8A8A8A")
check("@property", "fg", "#E49137")
check("@variable.parameter", "fg", "#D4D4D4")
check("@string.escape", "fg", "#00BBCC")
check("@tag", "fg", "#FE4864")

-- Cursor, selection, search.
check("Cursor", "bg", "#48AFFF")
check("TermCursor", "bg", "#48AFFF")
check("Visual", "bg", "#2F3C47")
check("CurSearch", "bg", "#2F3C47")
check("CurSearch", "fg", "#FFFFFF")

-- Live integrations: palette blue/pink intact through overrides.
check("DiagnosticInfo", "fg", "#48AFFF")
check("WhichKeyDesc", "fg", "#D4D4D4")
check("NoiceCmdlineIcon", "fg", "#48AFFF")
check("DiffAdd", "bg", "#2B4218")
check("DiffText", "bg", "#2D5E86")

-- Audit pins: markdown heading grounds neutral, chrome borders on surface-2
-- (btop's box grey).
check("RenderMarkdownH1Bg", "bg", "#262626")
check("BlinkCmpMenuBorder", "fg", "#3A3A3A")
check("WinSeparator", "fg", "#3A3A3A")
check("FloatBorder", "fg", "#3A3A3A")

-- Snacks terminal stays transparent like the editor.
check_nobg("SnacksNormal")
check_nobg("SnacksNormalNC")

-- Terminal ANSI (red/cursor codes).
check_gvar("terminal_color_0", "#202020")
check_gvar("terminal_color_1", "#FE4864")
check_gvar("terminal_color_4", "#48AFFF")
check_gvar("terminal_color_9", "#FF7376")

if failures > 0 then
  print(string.format("probe: %d FAILURES", failures))
  vim.cmd("cquit 1")
end
print("probe: all green")
vim.cmd("qa!")
