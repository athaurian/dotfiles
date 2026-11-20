# Installation

Installation proceeds in three stages. The host must satisfy the prerequisites
and configure the signed `forge` repository before the bootstrap target can
install packages and deploy the configuration. Each stage assumes that the
previous one is complete.

## Prerequisites

| Requirement                                                                                     | Purpose                                                                                                                                       |
| :---------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| Arch Linux or CachyOS on an [`x86-64-v3`](glossary.md#x86-64-v3) CPU (Haswell / Zen 1 or newer) | Packages in my custom repository are compiled with `-march=x86-64-v3` and will crash with [`SIGILL`](glossary.md#sigill) on older processors. |
| Any hostname                                                                                    | The hostname selects the desktop profile.                                                                                                     |
| `chezmoi`, `make`, `uv`, and `git` from the official repositories                               | The Python runner is needed before the package onboarding script starts.                                                                      |
| [`paru`](glossary.md#paru) from the [AUR](https://aur.archlinux.org/packages/paru)              | The onboarding script installs AUR packages with `paru` and exits `1` when it is absent.                                                      |
| The CachyOS repository                                                                          | Supplies `helium-browser-bin` and `vesktop-bin`; setup is described below.                                                                    |

The selection rule is given in [Machines](machines.md).

Building the AUR helper requires the base development group. Install the
bootstrap tools from the official repositories:

```bash
sudo pacman -S --needed chezmoi make uv git base-devel
```

### AUR helper (`paru`)

The onboarding script needs `paru` for the packages in the `aur` group. Without
it, the script installs the repository packages and then exits `1` after listing
the AUR packages for manual installation. Install it before bootstrapping:

```bash
git clone https://aur.archlinux.org/paru.git
cd paru
makepkg -si
```

### CachyOS repository

On plain Arch, the two packages in the `cachyos` group require the CachyOS
repository. CachyOS enables it by default. This step applies only to plain Arch.
The upstream script detects the CPU's instruction-set support and installs the
matching repository level:

```bash
curl https://mirror.cachyos.org/cachyos-repo.tar.xz -o cachyos-repo.tar.xz
tar xvf cachyos-repo.tar.xz
cd cachyos-repos
sudo ./cachyos-repo.sh
```

The script backs up `/etc/pacman.conf` before changing it. Verify that the
resulting configuration contains a `[cachyos]` stanza before continuing.

## 1. Add the `forge` package repository

I publish two desktop components, `calpdf-git` and `polybar-pinned`, in my
signed [`forge`](https://github.com/athaurian/forge) repository. Pacman cannot
use a signed repository until its key is present in the local keyring and marked
as trusted:

```bash
curl -fsSL https://athaurian.github.io/forge/signing_key.asc | sudo pacman-key --add -
sudo pacman-key --lsign-key 6E299CB692113F71A3ABC006EAC1C444324DD6C6
```

Append the repository to `/etc/pacman.conf`:

```ini
[forge]
SigLevel = Required DatabaseOptional
Server = https://athaurian.github.io/forge
```

Synchronize and upgrade your system packages:

```bash
sudo pacman -Syu
```

## 2. Bootstrap the dotfiles

Bootstrap is a single target that performs three operations in order:

1. Generate the derived files from `meta/palette.toml`.
2. Install the required packages.
3. Deploy the configuration to `$HOME`.

The two bootstrap targets differ only in the mode they record.

| Target       | Mode  |
| :----------- | :---- |
| `make dark`  | Dark  |
| `make light` | Light |

Both follow
[Mode switch behavior](system/palette-system.md#mode-switch-behavior).

```bash
chezmoi init https://github.com/athaurian/dotfiles
cd ~/.local/share/chezmoi
make dark
```

## 3. Update procedure

An update needs two applies. The update command pulls and applies in one step,
but the derived files it applies were generated before the pull and are
therefore stale with respect to the new commit. Regeneration followed by a
second apply corrects this.

1. Pull and apply: `chezmoi update`.
2. Enter the checkout: `cd ~/.local/share/chezmoi`.
3. Regenerate: `make palette`.
4. Install the regenerated files: `chezmoi apply`.

Regeneration in step 3 uses the mode recorded in `~/.local/state/palette-mode`.
