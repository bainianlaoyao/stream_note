from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sqlite3

from sqlalchemy.engine import make_url


def resolve_sqlite_file_path(database_url: str, base_dir: Path | None = None) -> Path | None:
    parsed_url = make_url(database_url)
    if parsed_url.get_backend_name() != "sqlite":
        return None

    database_name = parsed_url.database
    if database_name in (None, "", ":memory:"):
        raise ValueError("SQLite in-memory databases cannot be backed up or restored.")

    normalized_path = database_name
    if len(normalized_path) >= 3 and normalized_path[0] == "/" and normalized_path[2] == ":":
        normalized_path = normalized_path[1:]

    database_path = Path(normalized_path)
    if not database_path.is_absolute():
        root = base_dir if base_dir is not None else Path.cwd()
        database_path = root / database_path

    return database_path.resolve()


def build_backup_path(
    database_path: Path,
    backup_dir: Path,
    *,
    label: str,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    extension = database_path.suffix if database_path.suffix != "" else ".db"
    backup_name = f"{database_path.stem}.{label}.{timestamp}{extension}"
    return backup_dir / backup_name


def backup_sqlite_file(source_path: Path, backup_path: Path) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"Database file does not exist: {source_path}")

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(source_path)) as source_connection:
        with sqlite3.connect(str(backup_path)) as backup_connection:
            source_connection.backup(backup_connection)

    return backup_path.resolve()


def restore_sqlite_file(backup_path: Path, destination_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file does not exist: {backup_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(backup_path)) as backup_connection:
        with sqlite3.connect(str(destination_path)) as destination_connection:
            backup_connection.backup(destination_connection)
