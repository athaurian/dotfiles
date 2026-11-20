# Development

All tooling runs from the `chezmoi` checkout root because the Make targets refer
to repository-relative paths. The available entry points are listed in the
tables below.

## Repository layout

| Path                     | Contents                                                                  |
| :----------------------- | :------------------------------------------------------------------------ |
| `home/`                  | The `chezmoi` source tree; `.chezmoiroot` maps it onto `$HOME`            |
| `data/`                  | Inputs copied into the source: `packages.json` and charge-threshold rules |
| `meta/`                  | `palette.toml`, its generator, Neovim probes, and capture tooling         |
| `tests/`                 | Regression corpora that span scripts, such as `prettier-math`             |
| `docs/`                  | This documentation site, configured by `zensical.toml`                    |
| `overrides/`             | Site template overrides                                                   |
| `home/.chezmoidata.toml` | Hand-maintained fonts, theme and icon names, cursor, and X11 idle timings |

| Entry point | Purpose                    |
| :---------- | :------------------------- |
| `make help` | Enumerate all Make targets |

Some configuration must be kept identical in more than one location.

| Duplicated content                       | Locations that must change together                                                                                               |
| :--------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `forge` key import and repository stanza | [Installation](installation.md#1-add-the-forge-package-repository); `home/.chezmoiscripts/run_onchange_before_onboarding.sh.tmpl` |

## Package model

`data/packages.json` is the declarative source for package installation. The
onboarding script consumes five top-level keys:

| Key        | Installer | Contents                                                                                  | Failure behavior                           |
| :--------- | :-------- | :---------------------------------------------------------------------------------------- | :----------------------------------------- |
| `pacman`   | `pacman`  | Official-repository packages grouped into `desktop`, `system`, `tui`, `fonts`, and `apps` | —                                          |
| `cachyos`  | `pacman`  | Packages from the CachyOS repository                                                      | —                                          |
| `custom`   | `pacman`  | Packages from the `forge` repository                                                      | —                                          |
| `aur`      | `paru`    | AUR packages                                                                              | The script exits `1` when `paru` is absent |
| `machines` | `pacman`  | Per-hostname extras, with `thinkpad` as the fallback for other hosts                      | —                                          |

Three mechanisms keep package state consistent with the rest of the source tree.

| Mechanism                                    | Effect                                                                             |
| :------------------------------------------- | :--------------------------------------------------------------------------------- |
| Category flattening                          | The `pacman` categories collapse into one install set                              |
| [Trigger line](glossary.md#chezmoi-triggers) | Hashes `packages.json` to detect edits and rerun the script on the next apply      |
| Hostname test                                | Identical to the one in [`home/.chezmoiignore`](glossary.md#chezmoi-special-files) |

Because package selection and file deployment share one hostname test, a host
cannot receive one profile's packages with another profile's configuration.

## Formatting and linting

| Command       | Action                                             |
| :------------ | :------------------------------------------------- |
| `make format` | Rewrites tracked Markdown with the pinned Prettier |
| `make lint`   | Checks formatting without modifying files          |

## Checks

Each headless verification step has a dedicated target, which localizes a
failure to one component. `make check` runs the aggregate set in one command. It
has one ordering constraint: some checks render chezmoi templates that read the
derived palette files. Regeneration must precede them. Checks that require
machine state unavailable in CI are excluded and remain local.

| Target                     | Scope                                                                         | In aggregate | CI workflow  |
| :------------------------- | :---------------------------------------------------------------------------- | :----------- | :----------- |
| `make check`               | Runs the targets marked Yes below, beginning with `make palette`              | —            | Not used     |
| `make check-mpris`         | Ruff, mypy, and unit tests for the shared MPRIS poller                        | Yes          | `checks`     |
| `make check-sw`            | Ruff, mypy, and unit tests for the `sw` wallpaper utility                     | Yes          | `checks`     |
| `make check-calibre`       | Ruff, mypy, and unit tests for the Calibre sync scripts                       | Yes          | `checks`     |
| `make check-wlsunset`      | Ruff, mypy, and unit tests for `wlsunset-location`                            | Yes          | `checks`     |
| `make check-prettier-math` | Regression corpus for the `prettier-math` wrapper                             | Yes          | `checks`     |
| `make check-meta`          | Ruff, StyLua, and mypy for the repository tooling in `meta/`                  | Yes          | `checks`     |
| `make check-shell`         | ShellCheck and shfmt over repository shell scripts, rendering templates first | Yes          | `checks`     |
| `make check-nvim`          | StyLua over the Neovim Lua sources                                            | Yes          | `checks`     |
| `make check-launcher`      | Compiles the `launcher_dim` helper for Wayland and X11                        | Yes          | `checks`     |
| `make check-fonts`         | Asserts that the documentation site loads fonts from the shared theme         | Yes          | `build-site` |
| `make check-config`        | Runs each installed program's config validator against the applied files      | No           | Local only   |
| `make check-probe`         | Compares the deployed Neovim highlights against the palette                   | No           | Local only   |

| Local-only target   | Requirement                |
| :------------------ | :------------------------- |
| `make check-config` | An applied configuration   |
| `make check-probe`  | A live Neovim installation |

The `build-site` workflow additionally runs the formatting check and the site
build. Both rows appear in the Formatting and Site tables.

Regenerating tracked derived files can dirty the working tree. The regenerated
files must be committed together with the palette change that produced them.

| File class               | Tracked | Commit                              |
| :----------------------- | :------ | :---------------------------------- |
| Tracked derived files    | Yes     | With the originating palette change |
| `home/.chezmoidata.yaml` | No      | Never (gitignored)                  |

## Site and screenshots

| Target        | Action                                                                                                                                                   |
| :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `make site`   | Builds the documentation site into `site/` with `--strict`.                                                                                              |
| `make shots`  | Refreshes the automatic screenshot captures; see [Screenshots, lock, and idle](desktop/screenshots-lock-idle.md#regenerating-documentation-screenshots). |
| `make social` | Rebuilds the Open Graph banner.                                                                                                                          |
