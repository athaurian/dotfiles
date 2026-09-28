return {
  "folke/snacks.nvim",
  opts = {
    picker = {
      sources = {
        explorer = {
          hidden = true,
          win = {
            list = {
              keys = {
                ["Y"] = "yank_file_contents",
              },
            },
          },
          actions = {
            yank_file_contents = function(_, item)
              if not item or item.type == "dir" then
                return
              end

              local filepath = item.file
              local file = io.open(filepath, "r")
              if not file then
                vim.notify("Could not open file: " .. filepath .. ".", vim.log.levels.WARN)
                return
              end
              local content = file:read("*a")
              file:close()

              vim.fn.setreg("+", content)
              vim.fn.setreg('"', content)

              vim.notify("Yanked contents of: " .. vim.fn.fnamemodify(filepath, ":t") .. ".")
            end,
          },
        },
      },
    },
  },
}
