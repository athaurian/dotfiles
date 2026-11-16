# Shell

Bash is the login and interactive shell on both machines.

## Environment and readline behavior

- **Vi editing mode (`set -o vi`)**: Command-line editing uses Vi keybindings
  rather than Emacs defaults.
- **Clean project trees (`PYTHONPYCACHEPREFIX=~/.cache/python`)**: Redirects all
  `.pyc` bytecode caches into `~/.cache/python` so Python projects never
  accumulate `__pycache__` directories inside the working tree.
- **Default applications**: Sets `EDITOR=nvim`, `BROWSER=helium-browser`,
  `FILE_MANAGER=thunar`, `PASSWORD_MANAGER=keepassxc`, and
  `QT_QPA_PLATFORMTHEME=qt6ct`.
- **Night-light coordinates (`~/.config/wlsunset.env`)**: Loaded by
  `~/.bash_profile` when present, and read by `wlsunset.service` through
  `EnvironmentFile=`, so `wlsunset` starts without a network geolocation
  request.
- **Tool integrations**: Initializes `zoxide` (smart directory jumping), `fnm`
  (Node version manager), and `fzf` keybindings when installed.

## Notable aliases and functions

Standard `ls`, `git`, and navigation shortcuts live in `home/dot_bashrc`. The
helpers below have non-obvious or destructive behavior worth noting:

| Command    | Behavior                                                                                                                   |
| :--------- | :------------------------------------------------------------------------------------------------------------------------- |
| `cat`      | Aliased to `bat --theme=ansi` so syntax highlighting automatically follows the terminal's current light/dark ANSI palette. |
| `czp`      | Applies the `chezmoi` configuration and replaces the current shell with a new one.                                         |
| `hdel`     | **Destructive**: Deletes `~/.bash_history` after confirmation and replaces the current shell with a new one.               |
| `bak FILE` | Copies `FILE` to `FILE.bak.YYYYmmdd_HHMMSS`.                                                                               |
| `mkcd DIR` | Creates `DIR` (including parent directories) and `cd`s into it.                                                            |
