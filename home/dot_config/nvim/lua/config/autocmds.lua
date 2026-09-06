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

    -- Only start persistence if we are not being restored by the session manager.
    -- If the session manager handles snapshots, persistence can remain active,
    -- but the manager uses its own reduced snapshots rather than persistence files.
    if vim.g.NVIM_SESSION_MANAGER_RESTORED == "1" then
      -- The manager restored this instance; persistence should not overwrite
      -- the manager-owned snapshot.
      require("persistence").stop()
    else
      if vim.fn.argc() > 0 or vim.g.started_with_stdin then
        require("persistence").stop()
      end
    end
  end,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  -- Named like PersistenceAutoload. It reads and writes the handshake flags
  -- owned by the sway session manager (NVIM_SESSION_MANAGER_RESTORED,
  -- SnacksExplorerOpen). See session_manager_lib and dashboard.lua.
  group = vim.api.nvim_create_augroup("PersistenceCleanup", { clear = true }),
  callback = function()
    local explorer_open = 0

    local ok, picker = pcall(Snacks.picker.get, { source = "explorer" })
    if ok and picker[1] then
      explorer_open = 1
      picker[1]:close()
      vim.cmd("redraw")
    end

    -- This is preserved; the manager reads SnacksExplorerOpen independently.
    vim.g.SnacksExplorerOpen = explorer_open
  end,
})
