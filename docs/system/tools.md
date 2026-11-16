# Tools

Custom helper scripts installed to `~/.local/bin` (from `home/dot_local/bin/`).

## `prettier-math`, `format-docs`, and `format-vault`

Prettier `3.9.9` sometimes misparses `*` and `_` inside LaTeX math spans
(`$...$` and `$$...$$`) as Markdown emphasis, corrupting equations and breaking
table column widths when wrapping prose.

- **`prettier-math`**: Replaces inline and display math spans with fixed-width
  Unicode Private Use Area token strings of the exact same character length
  before invoking Prettier, then restores the original LaTeX math afterward.
  Preserving the exact character width keeps Markdown tables and line-length
  wrapping aligned.
- **`format-docs`**: Runs `prettier-math` across the workspace documentation and
  configuration files under `$HOME` selected by the script.
- **`format-vault`**: Runs `prettier-math` across the Obsidian vault at
  `~/Obsidian`, skipping `.obsidian`, `.trash`, `.stfolder`, and `.stversions`.
  **Note**: Both `format-docs` and `format-vault` rewrite matching files in
  place.

## `wlsunset-location`

Updates `~/.config/wlsunset.env` with `WLSUNSET_LATITUDE` and
`WLSUNSET_LONGITUDE` for `wlsunset.service` on `thinkpad` and `redshift.service`
on `optiplex`.

1. Queries the local D-Bus GeoClue2 service first.
2. If GeoClue2 is unavailable, falls back to HTTPS IP geolocation APIs
   (`ipinfo.io`, `get.geojs.io`, `ipapi.co` in order).

### Privacy and safety rules

- **VPN / proxy caveat**: When the GeoClue2 fallback triggers, the script makes
  outbound HTTPS requests to third-party IP geolocation services. If a VPN is
  active, the resolved coordinates will reflect the VPN exit node rather than
  your physical location.
- **Chezmoi source-tree protection**: Exits with code `3` when the target path
  is inside the `chezmoi` Git repository, so live location coordinates are never
  committed by accident.

| Exit code | Meaning                                                                   |
| :-------- | :------------------------------------------------------------------------ |
| `0`       | Coordinates written                                                       |
| `1`       | Usage error or invalid arguments                                          |
| `2`       | No location source succeeded (existing `wlsunset.env` is left unmodified) |
| `3`       | Output path is inside a Git or `chezmoi` source tree                      |

## Session wrappers (`wrapper_browser.sh` and `wrapper_polkit.sh`)

Launch the preferred browser (`helium-browser`, falling back to installed
Chromium/Firefox binaries) and the first available Polkit authentication agent
so Sway, i3, and systemd user units do not hardcode machine-specific binary
paths.
