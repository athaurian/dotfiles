# Desktop entries

Because a local entry shadows the system entry of the same name, an override can
change one launch property without patching the package. The two locations are:

| Entry source    | Location                             |
| :-------------- | :----------------------------------- |
| Local overrides | `home/dot_local/share/applications/` |
| System entries  | `/usr/share/applications/`           |

The overrides address three problems:

- toolkit theming,
- tiling window manager quirks,
- terminal launching from `fuzzel` or `rofi`.

## Local overrides

Each override changes one launch property of a system entry.

| Entry                                            | Override                                                  | Effect                                      |
| :----------------------------------------------- | :-------------------------------------------------------- | :------------------------------------------ |
| `btop.desktop`, `nvim.desktop`, `zellij.desktop` | Launch the TUI inside `kitty`; `btop` sets `--title=btop` | Terminal launching for the TUI applications |
| `org.keepassxc.KeePassXC.desktop`                | Prepends `env QT_QPA_PLATFORMTHEME=qt6ct` to `Exec=`      | Keeps the Qt palette correct                |
| `logisim-evolution.desktop`                      | Sets `_JAVA_AWT_WM_NONREPARENTING=1`                      | Makes Java menus render in tiling managers  |

The `btop` title is functional rather than cosmetic. Sway matches the title and
i3 matches the instance against a window rule that centers the terminal.

KeePassXC can be launched by D-Bus activation or by a desktop portal that did
not inherit `~/.bash_profile`. The override makes the Qt theme explicit so those
launch paths still follow the palette.

Java Swing and AWT assume a reparenting window manager. Without the environment
variable, Logisim's menus and dialogs appear as blank gray boxes under Sway and
i3.

## Default applications (`mimeapps.list`)

One default application is assigned per content category in the defaults file:

| Content               | Default application |
| :-------------------- | :------------------ |
| Web links             | `helium-browser`    |
| Directories           | `thunar`            |
| PDFs and EPUBs        | `zathura`           |
| Images                | `imv`               |
| Plain text and source | `nvim`              |
