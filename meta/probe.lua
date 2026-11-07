local here = vim.fs.dirname(debug.getinfo(1, "S").source:sub(2))
package.path = here .. "/?.lua;" .. package.path
local probe = require("probe_lib")

probe.headless("probe")
probe.load()
local p = probe.p

probe.check("Normal", "fg", p.text)
probe.check("Comment", "fg", p.muted)
probe.check_flag("Comment", "italic")
probe.check("@comment", "fg", p.muted)
probe.check("@property", "fg", p.orange)
probe.check("@variable.parameter", "fg", p.text)
probe.check("@string.escape", "fg", p.cyan)
probe.check("@tag", "fg", p.red)

probe.check("Cursor", "bg", p.blue)
probe.check("Cursor", "fg", p.on_accent)
probe.check("TermCursor", "bg", p.blue)
probe.check("Visual", "bg", p.selection)
probe.check("CurSearch", "bg", p.selection)
probe.check("CurSearch", "fg", p.text_max)

probe.check("DiagnosticInfo", "fg", p.blue)
probe.check("WhichKeyDesc", "fg", p.text)
probe.check("NoiceCmdlineIcon", "fg", p.blue)
probe.check("DiffAdd", "bg", p.diff_add)
probe.check("DiffText", "bg", p.diff_text)

probe.check("RenderMarkdownH1Bg", "bg", p.surface_0)
probe.check("BlinkCmpMenuBorder", "fg", p.surface_2)
probe.check("WinSeparator", "fg", p.surface_2)
probe.check("FloatBorder", "fg", p.surface_2)

probe.check_nobg("SnacksNormal")
probe.check_nobg("SnacksNormalNC")

probe.check_gvar("terminal_color_0", p.base)
probe.check_gvar("terminal_color_1", p.red)
probe.check_gvar("terminal_color_4", p.blue)
probe.check_gvar("terminal_color_9", p.red_bright)

probe.report("probe")
