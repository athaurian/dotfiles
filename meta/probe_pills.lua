local here = vim.fs.dirname(debug.getinfo(1, "S").source:sub(2))
package.path = here .. "/?.lua;" .. package.path
local probe = require("probe_lib")

probe.headless("probe_pills")
probe.load()
local p = probe.p

probe.check("MasonHighlightBlock", "bg", p.blue)
probe.check("MasonHighlightBlock", "fg", p.on_accent)
probe.check("MasonHighlightBlockBold", "bg", p.blue)
probe.check("MasonHighlightBlockBold", "fg", p.on_accent)
probe.check("LazyButtonActive", "bg", p.blue)
probe.check("LazyButtonActive", "fg", p.on_accent)

probe.check("MasonMutedBlock", "bg", p.surface_1)
probe.check("MasonMutedBlock", "fg", p.subtext)
probe.check("MasonMutedBlockBold", "bg", p.surface_1)
probe.check("MasonMutedBlockBold", "fg", p.subtext)
probe.check("MasonHeader", "bg", p.surface_1)
probe.check("MasonHeader", "fg", p.subtext)
probe.check("LazyButton", "bg", p.surface_1)
probe.check("LazyButton", "fg", p.subtext)

probe.check("LazyNormal", "bg", p.mantle)
probe.check("LazyH1", "fg", p.subtext)

probe.report("probe_pills")
