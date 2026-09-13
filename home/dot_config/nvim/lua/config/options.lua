-- Default options reference: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Session file contents. Keep in sync with the options list in
-- lua/plugins/persistence.lua. Both lists must match.
vim.o.sessionoptions = "buffers,curdir,folds,globals,help,tabpages,winsize,winpos,localoptions,skiprtp"

-- Mode-aware cursor: white beam for insert, purple block everywhere else.
-- Shapes and blink match the Neovim defaults; only the groups differ.
-- Neovim forwards each mode's cursor colors to the terminal (OSC 12), so
-- foot follows without its own per-mode setting.
vim.o.guicursor =
  "n-v-c:block-Cursor,i-ci-ve:ver25-CursorInsert,r-cr:hor20-Cursor,o:hor50-Cursor,a:blinkwait700-blinkoff400-blinkon250,sm:block-blinkwait175-blinkoff150-blinkon175"
