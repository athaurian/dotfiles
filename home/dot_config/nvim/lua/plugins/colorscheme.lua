-- One Dark on Neutral, locked (meta/color-scheme.md): One Dark hues ×1.5
-- via catppuccin overrides. Dark-only, static.

return {
  {
    "LazyVim/LazyVim",
    opts = { colorscheme = "catppuccin-mocha" },
  },
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    config = function()
      require("catppuccin").setup({
        flavour = "mocha",
        -- Transparent over wallpaper (foot uses same alpha).
        transparent_background = true,
        -- Keep bg-shade dim off: it paints NormalNC opaque, killing transparency.
        -- dim_inactive = { enabled = false, shade = "dark", percentage = 0.15 },
        -- term_colors = false,
        styles = { conditionals = {} },
        -- Live plugins only; rest auto-detect.
        integrations = {
          gitsigns = true,
          which_key = true,
          mason = true,
          noice = true,
          snacks = true,
          blink_cmp = { style = "bordered" },
        },
        color_overrides = {
          mocha = {
            rosewater = "#F2A256",
            flamingo = "#FE4864",
            pink = "#FF7376",
            mauve = "#D95AFC",
            red = "#FE4864",
            maroon = "#FE4864",
            peach = "#E49137",
            yellow = "#F4BC45",
            green = "#89C952",
            teal = "#00BBCC",
            sky = "#3DDAEE",
            blue = "#48AFFF",
            sapphire = "#48AFFF",
            lavender = "#E67FFF",
            text = "#D4D4D4",
            subtext1 = "#B3B3B3",
            subtext0 = "#8A8A8A",
            overlay2 = "#8A8A8A",
            overlay1 = "#3A3A3A",
            overlay0 = "#5A5A5A",
            surface2 = "#3A3A3A",
            surface1 = "#2D2D2D",
            surface0 = "#262626",
            base = "#202020",
            mantle = "#171717",
            crust = "#101010",
          },
        },
        custom_highlights = function(colors)
          return {
            -- Selection and cursor (rule 3).
            Visual = { bg = "#2F3C47" },
            Cursor = { bg = colors.blue, fg = colors.base },
            lCursor = { bg = colors.blue, fg = colors.base },
            CursorIM = { bg = colors.blue, fg = colors.base },
            TermCursor = { bg = colors.blue, fg = colors.base },
            CursorLine = { bg = colors.surface0 },
            CursorLineNr = { fg = colors.blue, style = { "bold" } },
            Search = { bg = "#2F3C47", fg = colors.text },
            IncSearch = { bg = colors.blue, fg = colors.base },
            CurSearch = { bg = "#2F3C47", fg = "#FFFFFF", style = { "bold" } },

            NormalNC = { bg = "none", fg = colors.subtext1 },

            -- rule 2.
            Comment = { fg = "#8A8A8A", style = { "italic" } },
            ["@comment"] = { fg = "#8A8A8A", style = { "italic" } },

            -- One Dark standard; catppuccin links differ.
            ["@variable.parameter"] = { fg = colors.text },
            ["@parameter"] = { fg = colors.text },
            ["@property"] = { fg = colors.peach },
            ["@variable.member"] = { fg = colors.peach },
            ["@field"] = { fg = colors.peach },
            ["@lsp.type.enumMember"] = { fg = colors.teal },
            ["@lsp.typemod.function.defaultLibrary"] = { fg = colors.teal },
            ["@string.escape"] = { fg = colors.teal },
            ["@string.special.symbol"] = { fg = colors.teal },
            ["@string.documentation"] = { fg = colors.green },
            ["@function.builtin"] = { fg = colors.teal },
            ["@function.macro"] = { fg = colors.peach },
            ["@constant.macro"] = { fg = colors.peach },
            ["@tag"] = { fg = colors.red },
            ["@tag.builtin"] = { fg = colors.red },
            ["@tag.attribute"] = { fg = colors.peach },
            ["@type.builtin"] = { fg = colors.yellow },
            ["@attribute"] = { fg = colors.blue },
            ["@constructor.python"] = { fg = colors.blue },
            ["@keyword.import.c"] = { link = "Include" },
            ["@keyword.import.cpp"] = { link = "Include" },
            PreProc = { fg = colors.mauve },
            Label = { fg = colors.red },
            Operator = { fg = colors.teal },

            -- Emphasis text, accent links (rule 3).
            ["@markup.strong"] = { fg = colors.text },
            ["@markup.italic"] = { fg = colors.text },
            ["@markup.link"] = { fg = colors.blue },
            ["@markup.link.label"] = { fg = colors.blue },
            ["@text.strong"] = { fg = colors.text },
            ["@text.emphasis"] = { fg = colors.text },
            ["@text.reference"] = { fg = colors.blue },
            ["@markup.quote"] = { fg = colors.overlay2 },
            ["@markup.list"] = { fg = colors.yellow },
            ["@markup.list.unchecked"] = { fg = colors.overlay2 },
            htmlH1 = { fg = colors.blue, style = { "bold" } },

            -- Single accent, bold (upstream blues all six).
            ["@markup.heading.1.markdown"] = { fg = colors.blue, style = { "bold" } },
            ["@markup.heading.2.markdown"] = { fg = colors.blue, style = { "bold" } },
            ["@markup.heading.3.markdown"] = { fg = colors.blue, style = { "bold" } },
            ["@markup.heading.4.markdown"] = { fg = colors.blue, style = { "bold" } },
            ["@markup.heading.5.markdown"] = { fg = colors.blue, style = { "bold" } },
            ["@markup.heading.6.markdown"] = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH1 = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH2 = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH3 = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH4 = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH5 = { fg = colors.blue, style = { "bold" } },
            RenderMarkdownH6 = { fg = colors.blue, style = { "bold" } },

            -- Chrome.
            FloatBorder = { fg = colors.overlay0, bg = colors.mantle },
            FloatTitle = { fg = colors.subtext1, bg = colors.mantle },
            WinSeparator = { fg = colors.overlay0 },
            StatusLineNC = { fg = colors.subtext0, bg = colors.mantle },
            TabLine = { bg = colors.crust, fg = colors.subtext1 },
            TabLineSel = { fg = colors.text, bg = colors.base, style = { "bold" } },
            Pmenu = { bg = colors.mantle, fg = colors.text },
            PmenuSel = { bg = colors.surface2, fg = "#FFFFFF", style = { "bold" } },
            PmenuBorder = { fg = colors.overlay0, bg = colors.mantle },
            MatchParen = { bg = colors.surface0 },
            QuickFixLine = { bg = colors.surface0 },
            Conceal = { fg = colors.overlay2 },
            Dimmed = { fg = colors.overlay2 },
            -- Backdrop for dim floats below (doc shadow role).
            BackdropDim = { bg = "#000000" },

            WhichKeyDesc = { fg = colors.text },
            WhichKeySeparator = { fg = colors.overlay2 },
            WhichKeyValue = { fg = colors.overlay2 },

            NoiceCmdlinePopupBorder = { fg = colors.overlay0 },
            NoiceCmdlineIcon = { fg = colors.blue },
            MasonHeader = { bg = colors.surface1, fg = colors.subtext1 },
            MasonHeading = { fg = colors.subtext1 },

            -- Lazy has no catppuccin integration; pin its ground/pills here.
            MasonHighlightBlock = { bg = colors.blue, fg = colors.base },
            MasonHighlightBlockBold = { bg = colors.blue, fg = colors.base },
            MasonMutedBlock = { bg = colors.surface1, fg = colors.subtext1 },
            MasonMutedBlockBold = { bg = colors.surface1, fg = colors.subtext1 },
            LazyNormal = { bg = colors.mantle },
            LazyButton = { bg = colors.surface1, fg = colors.subtext1 },
            LazyButtonActive = { bg = colors.blue, fg = colors.base },
            LazyH1 = { fg = colors.subtext1 },
            LazyH2 = { fg = colors.subtext1, style = { "bold" } },

            LspCodeLens = { fg = colors.overlay2 },
            LspInlayHint = { fg = colors.overlay2 },
            GitSignsCurrentLineBlame = { fg = colors.overlay2 },

            DiagnosticInfo = { fg = colors.blue },
            DiagnosticVirtualTextInfo = { fg = colors.blue },
            DiagnosticFloatingInfo = { fg = colors.blue },
            DiagnosticSignInfo = { fg = colors.blue },

            -- Kind icons match buffer semantics.
            BlinkCmpLabel = { fg = colors.text },
            BlinkCmpKindField = { fg = colors.peach },
            BlinkCmpKindProperty = { fg = colors.peach },
            BlinkCmpKindStruct = { fg = colors.yellow },

            SnacksNormal = { bg = colors.mantle },
            SnacksNormalNC = { bg = colors.mantle },
            SnacksPicker = { bg = colors.mantle },
            SnacksPickerBox = { bg = colors.mantle },
            SnacksPickerBorder = { fg = colors.overlay0, bg = colors.mantle },
            SnacksPickerTitle = { fg = colors.subtext1, bg = colors.mantle },
            SnacksPickerList = { bg = colors.mantle },
            SnacksPickerPreview = { bg = colors.base },
            SnacksPickerInput = { bg = colors.mantle },
            SnacksPickerSelected = { bg = colors.surface2, fg = "#FFFFFF", style = { "bold" } },
            SnacksPickerListCursorLine = { bg = colors.surface2, fg = colors.text, style = { "bold" } },
            SnacksPickerMatch = { fg = colors.blue, style = { "bold" } },
            SnacksPickerDir = { fg = colors.blue },
            SnacksPickerFile = { fg = colors.text },

            SnacksDashboardHeader = { fg = colors.peach, style = { "bold" } },

            -- Diffs (locked).
            DiffAdd = { bg = "#2B4218" },
            DiffChange = { bg = "#183D5A" },
            DiffDelete = { bg = "#391C1E" },
            DiffText = { bg = "#2D5E86" },
          }
        end,
      })

      local ansi = {
        [0] = "#202020",
        [1] = "#FE4864",
        [2] = "#89C952",
        [3] = "#F4BC45",
        [4] = "#48AFFF",
        [5] = "#D95AFC",
        [6] = "#00BBCC",
        [7] = "#D4D4D4",
        [8] = "#8A8A8A",
        [9] = "#FF7376",
        [10] = "#B9EE7D",
        [11] = "#FFD678",
        [12] = "#98C3FF",
        [13] = "#E67FFF",
        [14] = "#3DDAEE",
        [15] = "#FFFFFF",
      }

      for i, hex in pairs(ansi) do
        vim.g["terminal_color_" .. i] = hex
      end

      -- Mason/lazy skip dim floats when Normal has no bg; dim here.
      local backdrops = {}
      local backdrop_augroup = vim.api.nvim_create_augroup("backdrop-dim", { clear = true })
      for _, w in ipairs(vim.api.nvim_list_wins()) do
        local ok, whl = pcall(vim.api.nvim_get_option_value, "winhighlight", { win = w, scope = "local" })
        if ok and whl:find("BackdropDim", 1, true) then
          pcall(vim.api.nvim_win_close, w, true)
        end
      end
      vim.api.nvim_create_autocmd("FileType", {
        group = backdrop_augroup,
        pattern = { "mason", "lazy" },
        callback = function()
          local win = vim.api.nvim_get_current_win()
          vim.schedule(function()
            if not vim.api.nvim_win_is_valid(win) or backdrops[win] then
              return
            end
            local ft = vim.bo[vim.api.nvim_win_get_buf(win)].filetype
            if ft ~= "mason" and ft ~= "lazy" then
              return
            end
            local z = vim.api.nvim_win_get_config(win).zindex or 50
            local buf = vim.api.nvim_create_buf(false, true)
            local bwin = vim.api.nvim_open_win(buf, false, {
              relative = "editor",
              width = vim.o.columns,
              height = vim.o.lines,
              row = 0,
              col = 0,
              style = "minimal",
              focusable = false,
              zindex = math.max(z - 1, 1),
            })
            vim.api.nvim_set_option_value("winhighlight", "Normal:BackdropDim", { win = bwin, scope = "local" })
            vim.api.nvim_set_option_value("winblend", 60, { win = bwin, scope = "local" })
            vim.api.nvim_set_option_value("buftype", "nofile", { buf = buf, scope = "local" })
            backdrops[win] = bwin
          end)
        end,
      })
      vim.api.nvim_create_autocmd("WinClosed", {
        group = backdrop_augroup,
        callback = function(ev)
          local id = tonumber(ev.match)
          local bwin = id and backdrops[id]
          backdrops[id] = nil
          if bwin and vim.api.nvim_win_is_valid(bwin) then
            vim.api.nvim_win_close(bwin, true)
          end
        end,
      })
      vim.api.nvim_create_autocmd("VimResized", {
        group = backdrop_augroup,
        callback = function()
          for _, bwin in pairs(backdrops) do
            if vim.api.nvim_win_is_valid(bwin) then
              vim.api.nvim_win_set_config(bwin, { width = vim.o.columns, height = vim.o.lines })
            end
          end
        end,
      })
    end,
  },
}
