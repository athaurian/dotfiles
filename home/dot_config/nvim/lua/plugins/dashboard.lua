local header = "    |\\      _,,,---,,_     \n"
  .. "    /,`.-'`'    -.  ;-;;,_ \n"
  .. "   |,4-  ) )-,_..;\\ (  `'-'\n"
  .. "  '---''(_/--'  `-'\\_)     \n"
  .. "\n"
  .. "ネ  コ  ヴィ  ム\n"
  .. "ne  ko  vi    mu"

return {
  {
    "folke/snacks.nvim",
    opts = {
      dashboard = {
        -- Disable dashboard when the session manager restores a session.
        -- The manager launches Neovim with NVIM_RESTORE_SESSION=1, so a
        -- restored instance skips the dashboard. See autocmds.lua.
        enabled = vim.env.NVIM_RESTORE_SESSION ~= "1",
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
