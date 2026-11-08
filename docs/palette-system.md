# Palette system

Every color in the desktop configuration comes from
[`meta/palette.toml`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.toml).
[`meta/palette.py`](https://github.com/athaurian/dotfiles/blob/main/meta/palette.py)
reads that file and writes the palette data every template consumes, so changing
a value there changes it across the whole desktop at once.

Most colors carry two values, one for dark mode and one for light mode. The
exceptions are the two utility colors, which have one value each, and the tints
that derive from another color instead of being written by hand.

<figure class="screenshot">
  <img src="images/palette.webp" alt="A reference card showing every palette color token and hex value for dark and light modes.">
  <figcaption>Every palette value in both modes.</figcaption>
</figure>

The card above is a live capture rather than a rendered diagram. Rebuild it with
`make shots` after changing the palette, because nothing else regenerates it.

I use the [`Makefile`](https://github.com/athaurian/dotfiles/blob/main/Makefile)
targets to regenerate and apply the palette:

- The `palette` target regenerates the derived palette data without applying
  anything, so follow it with `chezmoi apply`.
- The `dark` and `light` targets regenerate the same data and apply the
  configuration in the chosen mode.

Don't hand-edit the generated files — the palette data every template reads and
the look-up table (LUT) palettes under
[`home/dot_config/lutgen/`](https://github.com/athaurian/dotfiles/tree/main/home/dot_config/lutgen/)
— because regeneration replaces them. The data file is gitignored, so it only
exists on a machine that has run the generator.
[`meta/lut-palette.md`](https://github.com/athaurian/dotfiles/blob/main/meta/lut-palette.md)
describes how the tables are built.

A few literals sit outside the palette on purpose: the shell prompt's ANSI
colors, the black fill behind the blurred lock screen, and the palette card's
panel background. This documentation site is self-themed too, because
[`docs/stylesheets/extra.css`](https://github.com/athaurian/dotfiles/blob/main/docs/stylesheets/extra.css)
uses a warm-paper light scheme of its own.
