# Installation

This section walks you through installing these dotfiles on a fresh machine,
step by step. It covers the packages you need, the theme build, and the config
files.

It assumes you are comfortable running commands in a terminal, and nothing else.
The tools that are central to this setup are explained when they first appear.

## Overview

This repository is a collection of dotfiles, which are the configuration files
that shape how your tools look and behave. They are managed by
[chezmoi](https://chezmoi.io), a tool that stores those files in a source
directory and installs copies into your home directory.

When you run `chezmoi apply`, chezmoi reads the source files and writes them to
the right places. Some source files are templates with a `.tmpl` extension. They
are filled in at apply time with data from `.chezmoidata.yaml`, a generated file
that carries your theme colors and other settings.

## Assumptions

This setup assumes your environment already has the following:

- Arch Linux (CachyOS preferred)
- Wayland, not X11
- `bash` as the interactive shell
- systemd user services

CachyOS is an Arch-based distribution tuned for performance. Wayland is the
display protocol that most Linux desktops use, and X11 is its older predecessor.
The window manager, the program that draws and arranges your windows, is SwayFX,
which is built on Wayland. `bash` is the shell, the program that reads the
commands you type in a terminal. systemd user services are background programs
that systemd starts for your user account, instead of for the whole machine.

The setup targets Arch-based systems, so other distributions might need
adjustments.

## The forge repository

> [!CAUTION] The packages served by my `forge` repository are compiled with
> `x86-64-v3` optimizations. They do not run on older generic `x86_64` CPUs.

Most Arch packages come from the official repositories, but some of the things
this setup needs are not packaged there. They are built and served from `forge`,
my own package repository, hosted under the same GitHub account as these
dotfiles. The GTK theme, the fonts, and a few utilities come from there, so you
must configure it before anything else can happen. You must add the `forge`
repository to `/etc/pacman.conf` and import its GPG key into pacman's keyring
before running `chezmoi apply`. The onboarding script fails and provides the
copy-paste commands if it detects that the repository is missing.

## Install the configuration

### Initialize the repository

Clone the repository with the following command:

```sh
chezmoi init https://github.com/athaurian/dotfiles
```

`chezmoi init` clones the repository and prepares it as your dotfiles source. It
does not modify any of your existing files.

### Add the forge repository

Add the `forge` repository and its key if you have not done so already:

```sh
sudo pacman-key --add <(curl -fsSL https://athaurian.github.io/forge/signing_key.asc)
sudo pacman-key --lsign-key 45EAC3E28FC392FC4418F415C0C5B611BF77F6E5
echo -e '\n[forge]\nSigLevel = Required DatabaseOptional\nServer = https://athaurian.github.io/forge' | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

_GNU Privacy Guard_ (_GPG_) is the encryption system used to sign and verify
packages. The first two commands trust the repository's signing key, the third
adds the repository to pacman's configuration, and the last one syncs your
package database so pacman can resolve `forge` packages. The `<(...)` form feeds
the output of the command inside as a file, and `tee -a` appends the echoed
lines to `/etc/pacman.conf`.

### Build your palette

A palette is a named collection of colors. `make dark` is a shortcut defined in
the `Makefile` at the root of the repository. It runs the palette build script,
which validates the colors and exports the dark variant into
`.chezmoidata.yaml`.

Build the dark palette:

```sh
make dark
```

### Apply the configs

`chezmoi apply` reads everything, renders every template, and installs the
result.

Install the rendered configs:

```sh
chezmoi apply
```

## Finish the setup

The `run_onchange_` onboarding script installs needed packages automatically.
The user systemd services are connected with `symlink_` files, which place them
in `sway-session.target.wants/` so the session target starts them automatically.

Each prefix has a distinct meaning:

- Scripts that start with `run_onchange_` are chezmoi hooks. They run whenever
  their source file changes, which suits one-time setup work.
- Files that start with `symlink_` are installed as symbolic links. The links
  that land in `sway-session.target.wants/` make systemd start those services
  together with `sway-session.target`, the unit that groups the session
  services.

## Package management

The full package manifest is in `home/.chezmoidata/packages.yaml`. To add a
package, edit `packages.yaml` and re-apply. The installer re-runs whenever the
manifest changes and skips whatever is already installed.

### Portability

This setup targets CachyOS, but the manifest is written so it works on plain
Arch as well. The packages are split into four sections, named after where they
come from:

- **`pacman`.** Packages from the official Arch repositories. The names are the
  same everywhere, so these need no attention on either distribution.
- **`cachyos`.** Packages that exist only in the CachyOS repositories, such as
  `vesktop` and `helium-browser-bin`. On plain Arch the same names exist in the
  AUR, so the installer pulls them from there.
- **`aur`.** Packages that exist only in the AUR, such as `topgrade-bin`. These
  need `paru` or a manual install.
- **`custom`.** Packages built in my `forge` repository. The closest plain-Arch
  source for each one is noted as a comment in `packages.yaml`.

Package names can differ slightly between CachyOS and plain Arch. The manifest
accounts for those differences in each section, so you do not have to adjust the
names yourself.

`paru` is a helper that installs packages from the _Arch User Repository_
(_AUR_), which is where community-maintained packages live. When it is present,
the onboarding script can install everything in one pass. When it is not, the
onboarding script installs the packages from the official repositories and
`forge` with pacman, then prints the AUR packages for you to install by hand. On
plain Arch, install `paru` first, so the CachyOS packages can resolve from the
AUR.
