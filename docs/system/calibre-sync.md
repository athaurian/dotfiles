# Calibre sync

The Calibre library is mirrored to Google Drive through an intermediate copy
rather than directly. Calibre's nested layout is a poor transfer format. For
that reason, the sync first flattens the library into a staging directory and
then makes the remote folder match that directory. The remote folder is
therefore a derived artifact: it is rewritten from the staging directory on
every run and has no state of its own. The sync runs on `thinkpad` only.

| Role              | Location                                   |
| :---------------- | :----------------------------------------- |
| Local library     | `~/Library`                                |
| Staging directory | `~/.cache/calibre-drive-sync/flat`         |
| Remote folder     | `gdrive:Books`                             |
| Entry point       | `calibre-drive-sync`                       |
| Transport         | [`rclone`](../glossary.md#rclone), one-way |

## Flat staging directory

Calibre stores books in deep `Author/Title (ID)/Title - Author.ext`
subdirectories. For easier browsing on mobile Google Drive clients and
e-readers, each book is hardlinked or copied into one flat directory with a
human-readable filename assembled from its metadata:

```text
Author - Series 01 - Title [short-hash].ext
```

| Filename component | Source                         |
| :----------------- | :----------------------------- |
| Author             | Book author                    |
| Series             | Series name and series index   |
| Title              | Book title                     |
| Short hash         | Disambiguates duplicate titles |

The hash also lets the script detect renamed metadata without re-uploading
unchanged book payloads.

## Sync behavior and warnings

The following behavior applies to scheduled runs as well as manual ones.

- **One-way destructive remote sync**: The final step deletes every remote file
  that is absent from the local staging directory. Never store files in
  `gdrive:Books` unless they originate in `~/Library`.
- **`--dry-run` still updates local cache files**: No remote Google Drive
  changes occur, but the staging directory and
  `~/.cache/calibre-drive-sync/library.json` are rebuilt.

## Schedule and manual commands

Two triggers start the same service. The timer bounds how stale the remote copy
can become; the reconnection trigger avoids waiting for the next timer tick
after the laptop has been offline.

| Trigger      | Unit                          | Condition      |
| :----------- | :---------------------------- | :------------- |
| Timer        | `calibre-sync.timer`          | Every 30 min   |
| Reconnection | `calibre-sync-netmon.service` | Sequence below |

| Parameter                         | Value      |
| :-------------------------------- | :--------- |
| Settling delay after reconnection | 10 seconds |
| Minimum spacing between triggers  | 2 minutes  |

The reconnection trigger proceeds in order:

1. NetworkManager reports a full connection.
2. The settling delay elapses.
3. The trigger is skipped if a sync is running or the spacing has not elapsed.
4. Connectivity is re-checked.
5. The sync service is started.

To trigger or test a sync manually:

```bash
# Full sync to gdrive:Books
calibre-drive-sync

# Rebuild local staging and preview what rclone would upload/delete
calibre-drive-sync --dry-run

# Check timer and recent sync logs
systemctl --user status calibre-sync.timer
journalctl --user -u calibre-sync.service -n 50
```
