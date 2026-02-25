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
)


def backup_database(
    *,
    database_url: str | None = None,
    backup_dir: Path | None = None,
    output: Path | None = None,
) -> Path:
    load_env_file()
    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", "sqlite:///./stream_note.db"
    )

    project_root = Path(__file__).resolve().parents[1]
    sqlite_path = resolve_sqlite_file_path(resolved_database_url, base_dir=project_root)
    if sqlite_path is None:
        raise ValueError("Only sqlite databases are supported by this backup script.")

    if output is None:
        target_backup_dir = backup_dir or (project_root / "backups")
        output = build_backup_path(
            sqlite_path, target_backup_dir, label="manual-backup"
        )

    return backup_sqlite_file(sqlite_path, output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a safe sqlite backup snapshot."
    )
    parser.add_argument(
        "--database-url", help="Override DATABASE_URL for this run.", default=None
    )
    parser.add_argument(
        "--backup-dir", help="Directory for generated backup files.", default=None
    )
    parser.add_argument(
        "--output", help="Explicit output backup file path.", default=None
    )
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None
    output = Path(args.output).resolve() if args.output else None

    backup_path = backup_database(
        database_url=args.database_url,
        backup_dir=backup_dir,
        output=output,
    )
    print(f"Backup created: {backup_path}")


if __name__ == "__main__":
    main()
