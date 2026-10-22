-- Reload the generated colorscheme in running instances. Chezmoi rewrites
-- lua/plugins/colorscheme.lua on every palette switch; watching that file
-- lets a mode toggle repaint Neovim without a restart.

local M = {}

local reloading = false
local attempts = 0

local function colorscheme_path()
  return vim.fn.stdpath("config") .. "/lua/plugins/colorscheme.lua"
end

local function entry(spec, key, value)
  for _, item in ipairs(spec) do
    if type(item) == "table" then
      if key == "name" and item.name == value then
        return item
      elseif key == "plugin" and item[1] == value then
        return item
      end
    end
  end
end

local function reload()
  reloading = false
  local ok, spec = pcall(dofile, colorscheme_path())
  if not ok or type(spec) ~= "table" then
    -- Chezmoi may still be writing the file; retry shortly.
    if attempts < 3 then
      attempts = attempts + 1
      reloading = true
      vim.defer_fn(reload, 200)
    end
    return
  end
  attempts = 0

  local catppuccin = entry(spec, "name", "catppuccin")
  if catppuccin and type(catppuccin.config) == "function" then
    if not pcall(catppuccin.config) then
      return
    end
  end

  local lazyvim = entry(spec, "plugin", "LazyVim/LazyVim")
  local scheme = lazyvim and lazyvim.opts and lazyvim.opts.colorscheme
  if scheme then
    vim.o.background = scheme:find("latte", 1, true) and "light" or "dark"
    pcall(vim.cmd.colorscheme, scheme)
  end
end

local function queue()
  if reloading then
    return
  end
  reloading = true
  attempts = 0
  -- Coalesce the burst of events chezmoi produces while applying.
  vim.defer_fn(reload, 100)
end

function M.watch()
  if M.handle then
    return
  end
  local uv = vim.uv or vim.loop
  if not uv.new_fs_event then
    return
  end
  local handle = uv.new_fs_event()
  if not handle then
    return
  end
  local dir = vim.fn.stdpath("config") .. "/lua/plugins"
  local ok = handle:start(dir, {}, function(err, filename)
    if err or (filename and filename ~= "colorscheme.lua") then
      return
    end
    vim.schedule(queue)
  end)
  if not ok then
    handle:close()
    return
  end
  M.handle = handle
  vim.api.nvim_create_autocmd("VimLeavePre", {
    once = true,
    callback = function()
      handle:stop()
      handle:close()
      M.handle = nil
    end,
  })
end

return M
