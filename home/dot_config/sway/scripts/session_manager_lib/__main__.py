"""CLI entry point."""

from __future__ import annotations

import argparse
import logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Sway session manager")
    parser.add_argument(
        "action",
        choices=["save", "restore", "has-session", "diff"],
        help="session action ('has-session' exits 0 when restorable content exists, 'diff' shows live vs saved)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="suppress desktop notifications",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="restore only this workspace (for example, --workspace 3)",
    )
    args = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=logging.INFO)
    quiet = args.quiet

    if args.action == "save":
        from .save import save_session

        save_session(notify_user=not quiet)
    elif args.action == "restore":
        from .restore import restore_session

        restore_session(notify_user=not quiet, workspace_filter=args.workspace)
    elif args.action == "diff":
        from .restore import diff_sessions

        diff_sessions()
    else:
        from .restore import has_restorable_content

        raise SystemExit(0 if has_restorable_content() else 1)


if __name__ == "__main__":
    main()
