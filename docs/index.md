---
template: home.html
---

# dotfiles

<div class="image-pair">
  <figure>
    <img src="images/hero.webp" alt="Neovim editing a Python test file, with its test output in a terminal split.">
  </figure>
  <figure>
    <img src="images/hero-empty.webp" alt="The desktop with no windows open.">
  </figure>
</div>

## Preface

Hi. This is the documentation I wrote for my dotfiles repository. If you'd
rather read the source code, it's on
[GitHub](https://github.com/athaurian/dotfiles).

The dotfiles themselves are managed with a neat tool called
[`chezmoi`](https://www.chezmoi.io/). Together they contain my setup for two
machines with conflicting hardware components.

The `thinkpad` laptop runs Sway on Wayland. Conversely, the `optiplex` desktop
runs i3 on X11. Both machines share the keybindings and the color palette.

Fortunately, `chezmoi` lets me separate the two machines in a single source
tree, so I didn't have to make two disjointed Git branches like a psycho. Once
everything is in place, each machine's hostname determines which files chezmoi
copies, which packages it installs, and which configuration I end up with.

I decided to make both light and dark modes because dark mode is awful to use
outdoors. I still like using it indoors, though.

As a final note, all of this is for people who are setting up or maintaining the
desktop, which is me (duh).

Start with [Installation](installation.md).

## Guides

Each guide covers one part of the desktop:

- [Installation](installation.md) sets up the prerequisites and the first apply.
- [Machines](machines.md) compares the components on `thinkpad` and `optiplex`.
- [Keybindings](keybindings.md) lists the window management bindings shared by
  both machines.
- [Palette system](palette-system.md) explains where every color in the system
  comes from.
- [Pickers](pickers.md) introduces the application launcher and the power
  shortcuts.
- [Screenshots, lock, and idle](screenshots-lock-idle.md) covers the capture,
  lock, and idle shortcuts.
- [Background services](services.md) explains which units start with each
  session.
- [Status bar](statusbar.md) describes Waybar on `thinkpad` and Polybar on
  `optiplex`.
- [Neovim](neovim.md) covers the LazyVim setup, plugins, and Discord presence.
- [Themes](theming.md) explains dark mode, light mode, and the wallpapers.
