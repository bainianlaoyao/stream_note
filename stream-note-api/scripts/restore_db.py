from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.core.env import load_env_file  # noqa: E402
from scripts.db_utils import (  # noqa: E402
    backup_sqlite_file,
    build_backup_path,
    resolve_sqlite_file_path,
    restore_sqlite_file,
)


def restore_database(
    *,
    backup_file: Path,
    database_url: str | None = None,
    skip_pre_restore_backup: bool = False,
) -> tuple[Path, Path | None]:
    load_env_file()
    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", "sqlite:///./stream_note.db"
    )

    project_root = Path(__file__).resolve().parents[1]
    sqlite_path = resolve_sqlite_file_path(resolved_database_url, base_dir=project_root)
    if sqlite_path is None:
        raise ValueError("Only sqlite databases are supported by this restore script.")

    pre_restore_backup: Path | None = None
    if sqlite_path.exists() and not skip_pre_restore_backup:
        pre_restore_backup = build_backup_path(
            sqlite_path,
            project_root / "backups",
            label="pre-restore",
        )
        backup_sqlite_file(sqlite_path, pre_restore_backup)

    restore_sqlite_file(backup_file.resolve(), sqlite_path)
    return sqlite_path, pre_restore_backup


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore sqlite DB from a backup snapshot."
    )
    parser.add_argument(
        "--backup-file", required=True, help="Backup database file to restore from."
    )
    parser.add_argument(
        "--database-url", help="Override DATABASE_URL for this run.", default=None
    )
    parser.add_argument(
        "--skip-pre-restore-backup",
        action="store_true",
        help="Skip creating a safety snapshot before restore.",
    )
    args = parser.parse_args()

    restored_path, pre_backup = restore_database(
        backup_file=Path(args.backup_file),
        database_url=args.database_url,
        skip_pre_restore_backup=args.skip_pre_restore_backup,
    )

    if pre_backup is not None:
        print(f"Pre-restore backup created: {pre_backup}")
    print(f"Database restored to: {restored_path}")


if __name__ == "__main__":
    main()
