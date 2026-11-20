# Tools

The helper scripts in `home/dot_local/bin/` are installed to `~/.local/bin`.
They fall into two groups.

| Group                        | Purpose                                           |
| :--------------------------- | :------------------------------------------------ |
| Markdown formatting wrappers | Protect LaTeX math spans from the pinned Prettier |
| Session helpers              | Resolve machine-specific values at runtime        |

## `prettier-math`, `format-docs`, and `format-vault`

The pinned Prettier release mistakes `*` and `_` inside LaTeX math spans for
Markdown emphasis. That misreading corrupts equations and alters table column
widths when prose wraps. The wrappers protect math spans before handing files to
Prettier, then restore them unchanged.

| Script          | Input set                        | Failure                         | Guarantee                                      |
| :-------------- | :------------------------------- | :------------------------------ | :--------------------------------------------- |
| `prettier-math` | Files passed on the command line | —                               | Single-line spans keep their character length  |
| `format-docs`   | `~/.config/prettier/docs.list`   | Exits `1` if the list is absent | The list is machine-local and outside the repo |
| `format-vault`  | `~/Obsidian`                     | —                               | See the skipped directories below              |

The wrapper protects formulas in three steps:

1. Replace inline and display math with Unicode Private Use Area tokens.
2. Run Prettier.
3. Restore the original LaTeX.

The vault formatter skips four directories:

- `.obsidian`
- `.trash`
- `.stfolder`
- `.stversions`

**Note**: Both `format-docs` and `format-vault` rewrite matching files in place.

## `wlsunset-location`

The location helper refreshes the coordinates consumed by the color-temperature
daemons on both machines.

| Property  | Value                                                              |
| :-------- | :----------------------------------------------------------------- |
| Output    | `~/.config/wlsunset.env`                                           |
| Variables | `WLSUNSET_LATITUDE`, `WLSUNSET_LONGITUDE`                          |
| Consumers | `wlsunset.service` on `thinkpad`, `redshift.service` on `optiplex` |

The location sources are tried in this order:

1. Explicit `--lat` and `--lon` values, when both are supplied.
2. [D-Bus](../glossary.md#d-bus) [GeoClue2](../glossary.md#geoclue2), which
   resolves the location without an outbound request.
3. `ipinfo.io`, `get.geojs.io`, and `ipapi.co`, in that order, when GeoClue2 is
   unavailable or returns no fix.

### Privacy and write-safety behavior

- **VPN / proxy caveat**: The fallback makes outbound HTTPS requests to
  third-party IP geolocation services. Coordinates then describe the VPN exit
  node instead of your physical location.
- **Source-tree protection**: Coordinates are live machine state. A write is
  refused when the output path lies inside any Git working tree or any source
  tree marked by chezmoi metadata. The exit status for that case is in the table
  below.

### Exit status

| Exit code | Meaning                                                                   |
| :-------- | :------------------------------------------------------------------------ |
| `0`       | Coordinates written                                                       |
| `1`       | Usage error or invalid arguments                                          |
| `2`       | No location source succeeded (existing `wlsunset.env` is left unmodified) |
| `3`       | Output path is inside a Git or `chezmoi` source tree                      |

## Session wrappers (`wrapper_browser.sh` and `wrapper_polkit.sh`)

Neither the compositors nor the systemd user units should hardcode
machine-specific binary paths. The wrappers resolve those paths at launch:

| Wrapper              | Selects                                                                  |
| :------------------- | :----------------------------------------------------------------------- |
| `wrapper_browser.sh` | `helium-browser`, falling back to Chromium or Firefox                    |
| `wrapper_polkit.sh`  | The first available [Polkit](../glossary.md#polkit) authentication agent |
