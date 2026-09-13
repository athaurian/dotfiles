-- Default autocmds reference: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua

local persistenceGroup = vim.api.nvim_create_augroup("PersistenceAutoload", { clear = true })

vim.api.nvim_create_autocmd("StdinReadPre", {
  group = persistenceGroup,
  callback = function()
    vim.g.started_with_stdin = true
  end,
})

vim.api.nvim_create_autocmd("VimEnter", {
  group = persistenceGroup,
  nested = true,
  callback = function()
    require("lazy").load({ plugins = { "persistence.nvim" } })

    -- Stop persistence for launches with file arguments or stdin, so the
    -- session only tracks bare, argumentless launches.
    if vim.fn.argc() > 0 or vim.g.started_with_stdin then
      require("persistence").stop()
    end
  end,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  -- Writes the SnacksExplorerOpen flag on exit for the <leader>qs keymap
  -- in persistence.lua.
  group = vim.api.nvim_create_augroup("PersistenceCleanup", { clear = true }),
  callback = function()
    local explorer_open = 0

    local ok, picker = pcall(Snacks.picker.get, { source = "explorer" })
    if ok and picker[1] then
      explorer_open = 1
      picker[1]:close()
      vim.cmd("redraw")
    end

    -- Preserved in persistence sessions by the globals option, so the
    -- <leader>qs keymap in persistence.lua can reopen the explorer.
    vim.g.SnacksExplorerOpen = explorer_open
  end,
})
