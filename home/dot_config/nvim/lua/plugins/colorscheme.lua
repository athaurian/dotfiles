-- Neutral base + One Dark chromatics, via catppuccin overrides.
-- Monochrome: the tmp-* neutrals plus two ramp steps (#101010 deep,
-- #262626 mid-surface) so floats, sidebars, editor, and panels each sit
-- on their own depth. Brightest step reuses tmp-border-inactive.
-- Chromatics: the Flint v3 "warmer One Dark" set, resolved statically from
-- 50c1062:palettes/flint/{dark,shared}.yaml. Dark-only, static.

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
        -- Opaque like the terminal; false so catppuccin never stomps
        -- the static ANSI table set below.
        transparent_background = false,
        term_colors = false,
        -- Explicit so every LazyVim surface is compiled from the
        -- palette below instead of falling back to stock groups.
        integrations = {
          gitsigns = true,
          which_key = true,
          mason = true,
          markdown = true,
          notify = true,
          noice = true,
          dap = true,
          dap_ui = true,
          telescope = true,
          neo_tree = true,
          snacks = true,
          indent_blankline = { enabled = true, scope_color = "overlay1" },
          blink_cmp = { style = "bordered" },
        },
        color_overrides = {
          mocha = {
            rosewater = "#DFAA7B",
            flamingo = "#E06C75",
            pink = "#F0A0A5",
            mauve = "#D890EA",
            red = "#E06C75",
            maroon = "#C62828",
            peach = "#D19A66",
            yellow = "#E5C07B",
            green = "#98C379",
            teal = "#56B6C2",
            sky = "#7DD3E0",
            sapphire = "#5865F2",
            blue = "#98C3FF",
            lavender = "#C678DD",
            text = "#D4D4D4",
            subtext1 = "#D4D4D4",
            subtext0 = "#B3B3B3",
            overlay2 = "#8A8A8A",
            overlay1 = "#5A5A5A",
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
            -- Selection and cursor.
            Visual = { bg = "#3A3F4B" },
            Cursor = { bg = "#61AFEF", fg = colors.base },
            CursorLine = { bg = colors.surface0 },
            CursorLineNr = { fg = colors.blue, style = { "bold" } },
            Search = { bg = colors.overlay1, fg = colors.base },
            IncSearch = { bg = colors.overlay1, fg = colors.base },

            -- Chrome: 1px borders in the fuzzel/waybar tone on dark fills.
            FloatBorder = { fg = colors.overlay0, bg = colors.mantle },
            FloatTitle = { fg = colors.subtext1, bg = colors.mantle },
            WinSeparator = { fg = colors.overlay0 },
            StatusLineNC = { fg = colors.subtext0, bg = colors.mantle },
            TabLine = { bg = colors.crust, fg = colors.subtext1 },
            TabLineSel = { fg = colors.text, bg = colors.base, style = { "bold" } },
            Pmenu = { bg = colors.mantle },
            PmenuSel = { bg = colors.surface2, fg = "#FFFFFF", style = { "bold" } },
            PmenuBorder = { fg = colors.overlay0, bg = colors.mantle },

            -- Telescope panels on the editor base, bordered.
            TelescopeBorder = { fg = colors.overlay0, bg = colors.base },
            TelescopePromptBorder = { fg = colors.overlay0, bg = colors.base },
            TelescopeResultsBorder = { fg = colors.overlay0, bg = colors.base },
            TelescopePreviewBorder = { fg = colors.overlay0, bg = colors.base },
            TelescopeSelection = { bg = colors.surface2, fg = colors.text, style = { "bold" } },
            TelescopeSelectionCaret = { bg = colors.surface2, fg = colors.blue },
            TelescopeMatching = { fg = colors.blue, style = { "bold" } },
            TelescopePreviewLine = { bg = colors.surface0 },

            -- Snacks picker: panels one step up, preview on the base.
            SnacksNormal = { bg = colors.mantle },
            SnacksNormalNC = { bg = colors.mantle },
            SnacksPicker = { bg = colors.surface1 },
            SnacksPickerBox = { bg = colors.surface1 },
            SnacksPickerBorder = { fg = colors.overlay0, bg = colors.surface1 },
            SnacksPickerTitle = { fg = colors.subtext1, bg = colors.surface1 },
            SnacksPickerList = { bg = colors.surface1 },
            SnacksPickerPreview = { bg = colors.base },
            SnacksPickerInput = { bg = colors.surface1 },
            SnacksPickerSelected = { bg = colors.surface2, fg = "#FFFFFF", style = { "bold" } },
            SnacksPickerListCursorLine = { bg = colors.surface2, fg = colors.text, style = { "bold" } },
            SnacksPickerMatch = { fg = colors.blue, style = { "bold" } },
            SnacksPickerDir = { fg = colors.teal },
            SnacksPickerFile = { fg = colors.text },

            -- File trees.
            NeoTreeCursorLine = { bg = colors.surface2, fg = colors.text, style = { "bold" } },
            NeoTreeDirectoryName = { fg = colors.teal },
            NeoTreeDirectoryIcon = { fg = colors.blue },
            NeoTreeRootName = { fg = colors.mauve, style = { "bold" } },
            NeoTreeFileName = { fg = colors.text },
            NeoTreeIndentMarker = { fg = colors.overlay2 },
            NeoTreeGitModified = { fg = colors.yellow },
            NeoTreeGitAdded = { fg = colors.green },
            NeoTreeGitDeleted = { fg = colors.red },
            NeoTreeWinSeparator = { link = "WinSeparator" },

            -- Dashboard (pre-reset: peach header).
            SnacksDashboardHeader = { fg = colors.peach, style = { "bold" } },

            -- Diffs (v3 depths).
            DiffAdd = { bg = "#2B4632" },
            DiffChange = { bg = "#1F3A52" },
            DiffDelete = { bg = "#332024" },
            DiffText = { bg = "#2C5372" },
          }
        end,
      })

      local ansi = {
        [0] = "#202020",
        [1] = "#E06C75",
        [2] = "#98C379",
        [3] = "#E5C07B",
        [4] = "#61AFEF",
        [5] = "#C678DD",
        [6] = "#56B6C2",
        [7] = "#D4D4D4",
        [8] = "#8A8A8A",
        [9] = "#F0A0A5",
        [10] = "#C4E8A0",
        [11] = "#F5D898",
        [12] = "#98C3FF",
        [13] = "#E3A2F8",
        [14] = "#7DD3E0",
        [15] = "#FFFFFF",
      }

      for i, hex in pairs(ansi) do
        vim.g["terminal_color_" .. i] = hex
      end
    end,
  },
}
