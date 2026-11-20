# Shell

Bash is the login and interactive shell on both machines. The configuration sets
readline behavior, environment defaults, and a small number of helpers.

## Environment and readline behavior

Each setting changes one aspect of the interactive shell or of child processes.

| Setting                | Value                    | Effect                                                              |
| :--------------------- | :----------------------- | :------------------------------------------------------------------ |
| `set -o vi`            | Vi editing mode          | Command-line editing uses Vi keybindings rather than Emacs defaults |
| `PYTHONPYCACHEPREFIX`  | `~/.cache/python`        | Python bytecode caches are kept outside the working tree            |
| `EDITOR`               | `nvim`                   | Default editor                                                      |
| `BROWSER`              | `helium-browser`         | Default browser                                                     |
| `FILE_MANAGER`         | `thunar`                 | Default file manager                                                |
| `PASSWORD_MANAGER`     | `keepassxc`              | Default password manager                                            |
| `QT_QPA_PLATFORMTHEME` | `qt6ct`                  | Qt theme platform                                                   |
| `zoxide`               | Initialized when present | Directory jumping ranked by frequency and recency                   |
| `fnm`                  | Initialized when present | Node version management                                             |
| `fzf`                  | Initialized when present | Fuzzy completion and keybindings                                    |

Coordinates are cached in one file so that no consumer has to issue a
geolocation request at startup. The writer is documented under
[`wlsunset-location`](../system/tools.md#wlsunset-location).

| Property   | Value                    |
| :--------- | :----------------------- |
| Cache file | `~/.config/wlsunset.env` |

| Consumer                  | Mechanism                                |
| :------------------------ | :--------------------------------------- |
| Shell (`~/.bash_profile`) | Loads the file when it exists            |
| Color-temperature daemons | Read the file through `EnvironmentFile=` |

## Notable aliases and functions

Standard shortcuts are kept in a separate file from the main startup file.

| File                         | Role                                           |
| :--------------------------- | :--------------------------------------------- |
| `home/dot_bash_aliases.tmpl` | Standard `ls`, `git`, and navigation shortcuts |
| `home/dot_bashrc`            | Sources the aliases file                       |

The helpers below have non-obvious or destructive behavior.

| Command    | Behavior                                                                                                                             |
| :--------- | :----------------------------------------------------------------------------------------------------------------------------------- |
| `cat`      | Aliased to `bat --theme=ansi` so syntax highlighting follows the terminal's current light/dark ANSI palette                          |
| `czp`      | Applies the `chezmoi` configuration and replaces the current shell so that the new environment takes effect                          |
| `hdel`     | **Destructive**: Deletes `~/.bash_history` after confirmation and replaces the current shell so that the old history is not reloaded |
| `bak FILE` | Copies `FILE` to `FILE.bak.YYYYmmdd_HHMMSS`                                                                                          |
| `mkcd DIR` | Creates `DIR` (including parent directories) and changes into it                                                                     |
