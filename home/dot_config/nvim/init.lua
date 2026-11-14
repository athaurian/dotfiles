-- Mason's servers need node; fnm provides it only in interactive shells.
local fnm_bin = vim.fn.expand("~/.local/share/fnm/aliases/default/bin")
if vim.fn.executable("node") == 0 and vim.fn.isdirectory(fnm_bin) == 1 then
  vim.env.PATH = fnm_bin .. ":" .. vim.env.PATH
end

require("config.lazy")
