# Troubleshooting

This page collects failure modes that cannot be diagnosed from the source tree
alone. Start from the symptom that matches what you observe.

## Orphaned files after `chezmoi apply`

**Symptom.** A file removed or renamed in `home/` still exists on a machine that
previously received it.

**Mechanism.** Applying a source state creates and updates destination files; it
does not infer deletion from absence in the source. A removed file therefore
becomes an orphan on every machine that already has it.

**Remedies.** Choose one:

1. Delete the obsolete copy by hand on each affected machine.
2. List the path in a removal file so that apply deletes it everywhere.

| File             | Location                 | Note                                                     |
| :--------------- | :----------------------- | :------------------------------------------------------- |
| `.chezmoiremove` | The source root, `home/` | A path listed here and in the ignore file is not removed |
| `.chezmoiignore` | The source root, `home/` | Takes precedence over a removal entry                    |

## Stale palette or incorrect mode

| Property           | Value                         |
| :----------------- | :---------------------------- |
| Path               | `~/.local/state/palette-mode` |
| Valid values       | `dark`, `light`               |
| Missing or unknown | Treated as `dark`             |

A corrupt state file degrades to the default mode rather than disabling theming.

The targets differ in which state they change. The comparison below is repeated
from [Mode switch behavior](system/palette-system.md#mode-switch-behavior).

| Command                               | Mode file written | Files regenerated | Live desktop changed |
| :------------------------------------ | :---------------- | :---------------- | :------------------- |
| `make dark` / `make light`            | Yes               | Yes               | Yes                  |
| `make palette MODE=dark` (or `light`) | No                | Yes               | No                   |
| `make shots`                          | Yes               | Yes               | Yes                  |

The last row records the intermediate state: the screenshot run switches modes
to capture both variants and restores the original mode on exit.

Apply and regeneration touch different state. A regenerated file has no effect
until it is applied.

| Operation       | Reads                         | Writes   | Regenerates derived files | Deletes obsolete destinations |
| :-------------- | :---------------------------- | :------- | :------------------------ | :---------------------------- |
| `chezmoi apply` | Source tree and derived files | `$HOME`  | No                        | No                            |
| `make palette`  | `meta/palette.toml`           | Checkout | Yes                       | Not applicable                |

To propagate an edit of `meta/palette.toml`, the single source file for palette
tokens, use one of two paths:

1. Regenerate with `make palette`, then apply with `chezmoi apply`.
2. Regenerate and apply in one step with `make dark` / `make light`. See
   [Mode switch behavior](system/palette-system.md#mode-switch-behavior).

## Failure during package installation

The onboarding script reports the first unmet prerequisite and exits non-zero.
Each message identifies a distinct failure:

| Message                                               | Cause                           | Corrective action                                                                                           |
| :---------------------------------------------------- | :------------------------------ | :---------------------------------------------------------------------------------------------------------- |
| `custom 'forge' repository is not configured`         | The repository stanza is absent | Complete [step 1 of the installation guide](installation.md#1-add-the-forge-package-repository).            |
| `paru not found, install these AUR packages manually` | The AUR helper is missing       | Install `paru`, then run `make dark` or `make light` again.                                                 |
| `uv not found`                                        | The Python runner is missing    | Install `uv` from the official repositories. Both mode-switch targets and the onboarding script require it. |

## Inactive user service

A unit that fails to start is diagnosed in three steps. `UNIT` stands for a unit
name from [Background services](system/services.md).

| Purpose        | Command                         |
| :------------- | :------------------------------ |
| Inspect status | `systemctl --user status UNIT`  |
| Read the log   | `journalctl --user -u UNIT -e`  |
| Restart        | `systemctl --user restart UNIT` |

| Machine    | Session target        |
| :--------- | :-------------------- |
| `thinkpad` | `sway-session.target` |
| `optiplex` | `i3-session.target`   |

[Compositor](glossary.md#compositor)-dependent units start after the machine's
[session target](glossary.md#session-target). Restart them from a terminal
inside the graphical session. A TTY does not provide the required Wayland or X11
environment. See [Background services](system/services.md) for the unit list.

## Changes that do not take effect

Inspect the difference between the source tree and `$HOME` before applying:

```bash
chezmoi diff
chezmoi apply --dry-run --verbose
```
