if #vim.api.nvim_list_uis() > 0 then
  io.stderr:write("probe_pills: refusing to run with a UI attached (headless only)\n")
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

check("MasonHighlightBlock", "bg", "#48AFFF")
check("MasonHighlightBlock", "fg", "#202020")
check("MasonHighlightBlockBold", "bg", "#48AFFF")
check("MasonHighlightBlockBold", "fg", "#202020")
check("LazyButtonActive", "bg", "#48AFFF")
check("LazyButtonActive", "fg", "#202020")

check("MasonMutedBlock", "bg", "#2D2D2D")
check("MasonMutedBlock", "fg", "#B3B3B3")
check("MasonMutedBlockBold", "bg", "#2D2D2D")
check("MasonMutedBlockBold", "fg", "#B3B3B3")
check("MasonHeader", "bg", "#2D2D2D")
check("MasonHeader", "fg", "#B3B3B3")
check("LazyButton", "bg", "#2D2D2D")
check("LazyButton", "fg", "#B3B3B3")

check("LazyNormal", "bg", "#171717")
check("LazyH1", "fg", "#B3B3B3")

if failures > 0 then
  print(string.format("probe_pills: %d FAILURES", failures))
  vim.cmd("cquit 1")
end
print("probe_pills: all green")
vim.cmd("qa!")
