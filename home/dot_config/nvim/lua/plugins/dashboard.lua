-- Logo comes from logo.txt; change spacing by editing that file.
local function read_logo()
  local file = io.open(vim.fn.stdpath("config") .. "/logo.txt", "r")
  if not file then
    return "neovim"
  end
  local lines = {}
  for line in file:lines() do
    lines[#lines + 1] = line
  end
  file:close()
  return #lines > 0 and table.concat(lines, "\n") or "neovim"
end

local header = read_logo()

return {
  {
    "folke/snacks.nvim",
    opts = {
      dashboard = {
        width = 30,
        preset = {
          header = header,
          keys = {
            { icon = "", key = "f", desc = "find file", action = ":lua Snacks.dashboard.pick('files')" },
            { icon = "", key = "n", desc = "new file", action = ":ene | startinsert" },
            { icon = "", key = "r", desc = "recent files", action = ":lua Snacks.dashboard.pick('oldfiles')" },
            { icon = "", key = "g", desc = "find text", action = ":lua Snacks.dashboard.pick('live_grep')" },
            { icon = "", key = "l", desc = "lazy", action = ":Lazy", enabled = package.loaded.lazy ~= nil },
            { icon = "", key = "q", desc = "quit", action = ":qa" },
          },
        },
      },
    },
  },
}
