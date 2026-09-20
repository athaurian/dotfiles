return {
  "folke/persistence.nvim",
  event = "BufReadPre",
  opts = {
    -- Session file contents. Keep in sync with vim.o.sessionoptions in
    -- lua/config/options.lua. Both lists must match.
    options = {
      "buffers",
      "curdir",
      "folds",
      "globals",
      "help",
      "tabpages",
      "winsize",
      "winpos",
      "localoptions",
      "skiprtp",
    },
  },
  keys = {
    {
      "<leader>qs",
      function()
        local ok, picker = pcall(Snacks.picker.get, { source = "explorer" })
        if ok and picker[1] then
          picker[1]:close()
        end

        require("persistence").load()

        if vim.g.SnacksExplorerOpen == 1 then
          vim.defer_fn(function()
            require("lazy").load({ plugins = { "snacks.nvim" } })
            pcall(Snacks.explorer)
          end, 100)
        end
      end,
      desc = "Restore Session",
    },
  },
}
