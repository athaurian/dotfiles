local edited_buffers = {}

local PRIVATE_MARKER = ".cordprivate"

-- A repo opts out of sharing its name and files by holding this file at its root.
local function repo_is_private(opts)
  local root = opts.workspace_dir or vim.uv.cwd()
  local marker = io.open(root .. "/" .. PRIVATE_MARKER, "r")
  if not marker then return false end
  marker:close()
  return true
end

local function repository_url(opts)
  if not opts.repo_url then return end
  if repo_is_private(opts) then return end
  local url = opts.repo_url:gsub("(https?://)[^/@]+@", "%1")
  return url
end

local function problems_suffix()
  local count = #vim.diagnostic.get(0, { severity = { min = vim.diagnostic.severity.WARN } })
  return string.format(" - %d %s found", count, count == 1 and "problem" or "problems")
end

local function setup_diagnostics(manager)
  vim.api.nvim_create_autocmd("DiagnosticChanged", {
    group = vim.api.nvim_create_augroup("CordProblems", { clear = true }),
    callback = function() manager:queue_update() end,
  })
end

local function setup_viewing(manager)
  local group = vim.api.nvim_create_augroup("CordViewing", { clear = true })

  vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI", "TextChangedP" }, {
    group = group,
    callback = function(args)
      if edited_buffers[args.buf] then return end
      edited_buffers[args.buf] = true
      manager:queue_update(true)
    end,
  })
  vim.api.nvim_create_autocmd("BufReadPost", {
    group = group,
    callback = function(args)
      edited_buffers[args.buf] = nil
      if args.buf ~= vim.api.nvim_get_current_buf() then return end
      manager:queue_update(true)
    end,
  })
  vim.api.nvim_create_autocmd({ "BufUnload", "BufWipeout" }, {
    group = group,
    callback = function(args) edited_buffers[args.buf] = nil end,
  })
end

local function apply_viewing(opts)
  if opts.filename == "" then return end
  local buf = vim.api.nvim_get_current_buf()
  if vim.bo[buf].modified then edited_buffers[buf] = true end
  opts.is_read_only = opts.is_read_only or not edited_buffers[buf]
end

-- snacks.bigfile replaces the filetype of huge buffers, hiding the real one.
local function resolve_bigfile(opts)
  if opts.filetype ~= "bigfile" then return end
  local filetype = vim.filetype.match({ buf = vim.api.nvim_get_current_buf() })
  if filetype and filetype ~= "bigfile" then opts.force_filetype = filetype end
end

return {
  "vyfor/cord.nvim",
  opts = {
    display = { theme = "atom", flavor = "accent", swap_fields = true },
    editor = { tooltip = "Neovim" },
    -- swap_fields also swaps idle fields; keep the state on the top line.
    idle = { details = "", state = "Idling" },

    text = {
      workspace = function(opts)
        if opts.private then return "In a private project" end
        local text = "In " .. opts.workspace
        if opts.type == "language" then
          text = text .. problems_suffix()
        end
        return text
      end,
      editing = function(opts)
        if opts.private then return "Working on a private file" end
        return string.format("Working on %s:%d:%d", opts.filename, opts.cursor_line, opts.cursor_char + 1)
      end,
      viewing = function(opts)
        if opts.private then return "Viewing a private file" end
        return "Viewing " .. opts.filename
      end,
      terminal = function(opts)
        if opts.private then return "Running commands in the terminal" end
        if opts.name and opts.name:lower() == "terminal" then
          return "Running commands in the terminal"
        end
        return "Running commands in " .. opts.name
      end,
      file_browser = function(opts)
        if opts.private then return "Browsing files" end
        if opts.name and opts.name:lower() == "picker" then
          return "Browsing files in the picker"
        end
        return "Browsing files in " .. opts.name
      end,
    },
    hooks = {
      ready = function(manager)
        setup_diagnostics(manager)
        setup_viewing(manager)
      end,
      pre_activity = function(opts)
        resolve_bigfile(opts)
        apply_viewing(opts)
        opts.private = repo_is_private(opts)
      end,
    },
    assets = {
      snacks_dashboard = { name = "Dashboard", tooltip = "Dashboard" },
      snacks_picker_input = { name = "Picker", tooltip = "Picker" },
      snacks_picker_list = { name = "Picker", tooltip = "Picker" },
      snacks_picker_preview = { name = "Picker", tooltip = "Picker" },
      snacks_terminal = { name = "Terminal", tooltip = "Terminal" },
    },
    buttons = {
      {
        label = "View Repository",
        url = repository_url,
      },
    },
  },
}
