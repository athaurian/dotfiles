# Applications

Most application files in `home/dot_config/` are generated or templated from
`meta/palette.toml`. This page therefore omits routine settings and records the
non-obvious behavior of post-apply hooks, notification routing, and font
precedence.

## Theme synchronization hook

The hook is `run_onchange_after_gtk-mode-hook.sh.tmpl`. A dark or light switch
triggers apply, which fires the hook for applications that keep theme state
outside plain dotfiles. Two of them need special handling.

Applications that read their palette once at startup need an explicit reload,
and each is reloaded by a different mechanism. The authoritative per-application
list is the table in
[Mode switch behavior](../system/palette-system.md#mode-switch-behavior). This
page documents only the two applications that need special handling.

| Application      | Condition   | Update behavior                    |
| :--------------- | :---------- | :--------------------------------- |
| GTK applications | Running     | GSettings keys are set             |
| Calibre          | Not running | Its UI palette config is rewritten |

[GSettings](../glossary.md#gsettings) stores state outside the dotfiles.
Rewriting configuration files alone would leave open applications unchanged.
Calibre rewrites its own configuration on exit. An edit during an open session
would therefore be lost.

The keys written for GTK applications are:

| GSettings key         | Dark mode             | Light mode             |
| :-------------------- | :-------------------- | :--------------------- |
| `color-scheme`        | `prefer-dark`         | `prefer-light`         |
| `gtk-theme`           | `Orchis-Dark-Compact` | `Orchis-Light-Compact` |
| `icon-theme`          | `Papirus-Dark`        | `Papirus-Light`        |
| `font-name`           | Sans font at 10 pt    | Sans font at 10 pt     |
| `document-font-name`  | Sans font at 10 pt    | Sans font at 10 pt     |
| `monospace-font-name` | Code font at 10 pt    | Code font at 10 pt     |

The theme and icon names in this table are hand-maintained in
`home/.chezmoidata.toml`, together with the font families used by the desktop.

## Notifications and Do Not Disturb (`dunst`)

Critical system alerts continue to appear when normal notifications are
silenced. The bar toggles between two pause levels, and a set of sources is
configured to bypass both.

| Pause level | Set by               | Effect                                |
| :---------- | :------------------- | :------------------------------------ |
| `0`         | Normal state         | Shows every notification              |
| `50`        | Do Not Disturb on    | Silences normal notifications         |
| `90`        | Sources listed below | Shown even while Do Not Disturb is on |

Six notification sources carry the level-90 override:

| Source            | Purpose                         |
| :---------------- | :------------------------------ |
| `dunst-dnd`       | Do Not Disturb toggles          |
| `caffeine-toggle` | Idle-inhibitor toggles          |
| `sw`              | Wallpaper errors                |
| `idle-warning`    | Idle timeout warnings           |
| `lock`            | Screen-lock and session actions |
| `screenshot`      | Capture results and failures    |

## Font priorities (`fonts.conf`)

- **Serif**: Merriweather is a weak `serif` preference. The weak binding leaves
  language-specific serif mappings intact for scripts that Merriweather does not
  cover, such as CJK.
- **Code**: GeistMono Nerd Font Mono supplies glyphs missing from Geist Mono,
  without replacing the requested family.
- **GTK applications**: Geist is used for UI text and Geist Mono for monospace
  text.

## Other configured tools

| Tool                               | Behavior                                                                              |
| :--------------------------------- | :------------------------------------------------------------------------------------ |
| Document viewer (`zathura`)        | Recolors PDF pages to match the active palette; `Ctrl+r` restores the original colors |
| Terminal stack (`kitty`, `zellij`) | A mode switch rewrites the theme files and signals kitty to repaint open windows      |
| Vesktop (Discord)                  | Pulls a generated QuickCSS theme file mapped from `meta/palette.toml`                 |
