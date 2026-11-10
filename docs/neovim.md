# Neovim

Neovim is my editor. I keep the configuration under
[`home/dot_config/nvim/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/nvim/).

I like it because its design is intentionally modest. I want an editor that
works exactly the way I expect without adding regular maintenance work.

<figure class="screenshot">
  <img src="images/hero.webp" alt="Neovim editing a Python test file, with its test output in a terminal split.">
</figure>

## Why LazyVim

I use LazyVim as a base instead of starting from scratch.

A configuration written from scratch would duplicate work that LazyVim already
does. LazyVim lets me keep my overrides small. I can spend more time actually
using the editor instead of learning Neovim's internals just to change its
behavior.

## Looking like the desktop

Neovim is the single most important piece in this setup, so I don't want it to
keep its default appearance.
[The Catppuccin theme](https://github.com/catppuccin/nvim) gives it a base
configuration I can edit to match my predefined palette in
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml).

Switching between light and dark updates the editor along with everything else.

<figure class="screenshot no-radius">
  <img src="images/neovim-editor-light.webp#only-light" alt="Neovim in light mode with the file explorer open on the left.">
  <img src="images/neovim-editor.webp#only-dark" alt="Neovim in dark mode with the file explorer open on the left.">
</figure>

## Discord presence

I had a lot of fun configuring the Cord plugin. I based the layout on the
[VSCord extension](https://github.com/LeonardSSH/vscord). Fortunately, Lua is
powerful enough that I can make an effort to match what it displays on Discord.

It shows `Viewing` until I edit the buffer. Once I start editing the file, it
switches to `Working on file:line:column` and appends the number of errors and
warnings. Also, when the repository I'm working in has a Git remote, it displays
a `View Repository` button that opens the repository in my browser.

I keep private repositories private by placing a `.cordprivate` file in the
repository root. Cord then replaces the project and file names with generic text
and removes the button.

<figure class="screenshot no-radius">
  <img src="images/neovim-discord-light.webp#only-light" alt="A Discord activity card showing Neovim editing a Python file in the chezmoi repository, with a View Repository button.">
  <img src="images/neovim-discord.webp#only-dark" alt="A Discord activity card showing Neovim editing a Python file in the chezmoi repository, with a View Repository button.">
</figure>
