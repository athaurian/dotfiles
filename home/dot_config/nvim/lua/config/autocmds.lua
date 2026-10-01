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

    if vim.fn.argc() > 0 or vim.g.started_with_stdin then
      require("persistence").stop()
    end
  end,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  group = vim.api.nvim_create_augroup("PersistenceCleanup", { clear = true }),
  callback = function()
    local explorer_open = 0

    local ok, picker = pcall(Snacks.picker.get, { source = "explorer" })
    if ok and picker[1] then
      explorer_open = 1
      picker[1]:close()
      vim.cmd("redraw")
    end

    vim.g.SnacksExplorerOpen = explorer_open
  end,
})
