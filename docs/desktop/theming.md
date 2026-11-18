# Theming

Press `$mod+Shift+t` at any time to toggle the desktop between dark and light
modes.

## How the live toggle works

1. Reads the current mode from `~/.local/state/palette-mode` (defaulting to
   `dark` if the file is missing) and flips it.
2. Runs the palette apply flow from `~/.local/share/chezmoi` (see
   [Palette system](../system/palette-system.md) for the underlying `make dark`,
   `make light`, and `make palette` targets).
3. Signals running applications to reload their colors in place:
   - **Sway / i3, Waybar / Polybar, and `dunst`**: Reload their updated
     configuration files.
   - **`kitty` and Neovim**: `kitty` repaints open windows from `SIGUSR1`;
     Neovim reloads the rewritten colorscheme through `lua/config/palette.lua`.
   - **GTK apps and Calibre**: Updated via the post-apply hook described in
     [Applications](applications.md#theme-synchronization-hook-run_onchange_after_gtk-mode-hookshtmpl).
   - **Wallpaper**: Recolored to match the new palette via
     [`sw`](wallpapers.md).
