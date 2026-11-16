# Calibre sync

On `thinkpad`, `calibre-drive-sync` exports books from the local Calibre library
(`~/Library`) into a flat staging folder (`~/.cache/calibre-drive-sync/flat`)
and syncs that folder one-way to `gdrive:Books` via `rclone`.

## Why it uses a flat staging directory

Calibre stores books in deep `Author/Title (ID)/Title - Author.ext`
subdirectories that are awkward to browse on mobile Google Drive clients or
e-readers. Staging hardlinks (or copies) every book into a single flat directory
with human-readable filenames sorted by author, series index, and title:

```text
Author - Series 01 - Title [short-hash].ext
```

The trailing hash disambiguates duplicate titles and lets the script detect
renamed metadata without re-uploading unchanged book payloads.

## Warnings before running manually

- **One-way destructive remote sync**: The final step runs `rclone sync`, which
  **deletes any file in `gdrive:Books` that is not present in the local staging
  directory**. Never store files in `gdrive:Books` unless they live in
  `~/Library`.
- **`--dry-run` still updates local cache files**: Passing `--dry-run` passes
  `--dry-run` to `rclone` so no remote Google Drive changes occur, **but it
  still rebuilds `~/.cache/calibre-drive-sync/flat` and updates
  `~/.cache/calibre-drive-sync/library.json` locally**.

## Schedule and manual commands

`calibre-sync.timer` runs automatically in the background on `thinkpad`. To
trigger or test a sync manually:

```bash
# Full sync to gdrive:Books
calibre-drive-sync

# Rebuild local staging and preview what rclone would upload/delete
calibre-drive-sync --dry-run

# Check timer and recent sync logs
systemctl --user status calibre-sync.timer
journalctl --user -u calibre-sync.service -n 50
```
