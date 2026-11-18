# Neovim

<figure class="screenshot">
  <img src="images/hero.webp" alt="Neovim editing a Python test file, with its test output in a terminal split.">
</figure>

Neovim is my editor. I keep its configuration under
[`home/dot_config/nvim/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/nvim/).

I like it because its design is intentionally modest. I want an editor that
works exactly the way I expect without adding regular maintenance work.

## Why LazyVim

A configuration written from scratch would duplicate work that LazyVim already
does. LazyVim lets me keep my overrides small. I can spend more time _actually_
using the editor instead of learning Neovim's internals just to change its
behavior.

## Live palette synchronization

<figure class="screenshot no-radius">
  <img src="images/neovim-editor-light.webp#only-light" alt="Neovim in light mode with the file explorer open on the left.">
  <img src="images/neovim-editor.webp#only-dark" alt="Neovim in dark mode with the file explorer open on the left.">
</figure>

Neovim uses `catppuccin` with its color slots overridden from
`meta/palette.toml`. When you press `$mod+Shift+t` or run `make dark` /
`make light`, chezmoi rewrites `~/.config/nvim/lua/plugins/colorscheme.lua`. The
watcher in `lua/config/palette.lua` reloads the colorscheme in every running
Neovim instance without a restart.

## Discord Rich Presence (`cord.nvim`)

<figure class="screenshot no-radius">
  <img src="images/neovim-discord-light.webp#only-light" alt="A Discord activity card showing Neovim editing a Python file in the chezmoi repository, with a View Repository button.">
  <img src="images/neovim-discord.webp#only-dark" alt="A Discord activity card showing Neovim editing a Python file in the chezmoi repository, with a View Repository button.">
</figure>

`cord.nvim` publishes the current editor activity to Discord. To suppress
workspace and file details inside sensitive repositories, create an empty
`.cordprivate` file at the root of that project:

```bash
touch .cordprivate
```

When `cord.nvim` detects `.cordprivate` in an ancestor directory, it replaces
the project name, filename, and repository button in your Discord status with a
generic editing message. (This only redacts Discord Rich Presence metadata.)
