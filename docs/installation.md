# Installation

This page walks through installing the dotfiles on a fresh machine.

## Overview

The repository is a collection of dotfiles managed by
[chezmoi](https://chezmoi.io), which stores them in a source directory and
installs them into the home directory. Some source files are `.tmpl` templates
that chezmoi renders at apply time with data such as the palette colors and the
package manifest.

## Assumptions

This setup assumes the following:

- Arch Linux (CachyOS preferred)
- Wayland, not X11
- `bash` as the interactive shell
- systemd user services

The window manager is SwayFX, which runs on Wayland. The setup targets
Arch-based systems, so other distributions need adjustments.

## The forge repository

> [!CAUTION] The packages served by the `forge` repository are compiled with
> `x86-64-v3` optimizations. They do not run on older generic `x86_64` CPUs.

Some packages are not in the official repositories. They come from `forge`, a
custom package repository hosted under the same GitHub account as these
dotfiles. The GTK theme, the fonts, and a few utilities come from there, so
configure it before anything else can happen. Add the repository and its signing
key to pacman:

```sh
sudo pacman-key --add <(curl -fsSL https://athaurian.github.io/forge/signing_key.asc)
sudo pacman-key --lsign-key 45EAC3E28FC392FC4418F415C0C5B611BF77F6E5
echo -e '\n[forge]\nSigLevel = Required DatabaseOptional\nServer = https://athaurian.github.io/forge' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

The first two commands import and locally sign the repository key, the third
appends the repository to pacman's configuration, and the last syncs the package
database so pacman can resolve `forge` packages. The `<(...)` form feeds the
output of the command inside it to pacman as a file.

## Install the configuration

Three commands install the configs:

1. Clone the repository into the chezmoi source directory:

   ```sh
   chezmoi init https://github.com/athaurian/dotfiles
   ```

2. Build the dark palette from the source directory:

   ```sh
   cd ~/.local/share/chezmoi
   make dark
   ```

3. Apply the configs:

   ```sh
   chezmoi apply
   ```

`chezmoi init` clones the repository and prepares the source directory without
modifying existing files. `make dark` runs the palette build script, which
validates the colors and writes `.chezmoidata.yaml`. The `chezmoi apply` command
renders every template and installs the result.

## Finish the setup

The `run_onchange_` onboarding script installs needed packages automatically.
Scripts that start with `run_onchange_` are chezmoi hooks that run whenever
their source file changes.

Files that start with `symlink_` install as symbolic links. The links in
`sway-session.target.wants/` point at the session services and make systemd
start them together with `sway-session.target`, the unit that groups the session
services.

## Package management

The full package manifest is in `home/.chezmoidata/packages.yaml`. Add a package
by editing the manifest and re-applying. The onboarding script re-runs when the
manifest changes and skips whatever is already installed.

Packages are split into four sections, named after where they come from:

- **`pacman`.** Packages from the official Arch repositories.
- **`cachyos`.** Packages that exist only in the CachyOS repositories, such as
  `vesktop`. On plain Arch the same names exist in the AUR, so the onboarding
  script needs `paru` to pull them from there.
- **`aur`.** Packages that exist only in the AUR, such as `topgrade-bin`. These
  need `paru` or a manual install.
- **`custom`.** Packages built in the forge repository, with the closest
  plain-Arch source noted as a comment in `packages.yaml`.

When `paru` is present, the onboarding script installs everything in one pass.
Without it, the script installs the pacman, cachyos, and forge packages, then
prints the AUR packages for a manual install.
