from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
import os
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.env import load_env_file  # noqa: E402
from app.models.database import Base  # noqa: E402
from app.models.migrations import run_startup_migrations  # noqa: E402
from app.models.schema_version import (  # noqa: E402
    BASELINE_REVISION,
    get_alembic_config,
    get_current_database_revision,
    get_head_revision,
)
from scripts.db_utils import (  # noqa: E402
    backup_sqlite_file,
    build_backup_path,
    resolve_sqlite_file_path,
)
import app.models  # noqa: F401,E402


@dataclass(frozen=True)
class MigrationResult:
    database_url: str
    previous_revision: str | None
    current_revision: str
    head_revision: str
    backup_path: Path | None


def _build_engine(database_url: str) -> Engine:
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args)


def _bootstrap_legacy_schema(engine: Engine) -> None:
    # Keep old deployments safe before stamping baseline revision.
    Base.metadata.create_all(bind=engine)
    run_startup_migrations(engine)


def migrate_database(
    *,
    database_url: str | None = None,
    backup_dir: Path | None = None,
    skip_backup: bool = False,
) -> MigrationResult:
    load_env_file()
    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", "sqlite:///./stream_note.db"
    )
    project_root = Path(__file__).resolve().parents[1]

    backup_path: Path | None = None
    sqlite_path = resolve_sqlite_file_path(resolved_database_url, base_dir=project_root)
    if sqlite_path is not None and sqlite_path.exists() and not skip_backup:
        target_backup_dir = backup_dir or (project_root / "backups")
        backup_path = build_backup_path(
            sqlite_path, target_backup_dir, label="pre-migration"
        )
        backup_path = backup_sqlite_file(sqlite_path, backup_path)

    engine = _build_engine(resolved_database_url)
    try:
        _bootstrap_legacy_schema(engine)

        previous_revision = get_current_database_revision(engine)
        config = get_alembic_config(resolved_database_url)

        if previous_revision is None:
            command.stamp(config, BASELINE_REVISION)
            previous_revision = BASELINE_REVISION

        command.upgrade(config, "head")

        current_revision = get_current_database_revision(engine)
        if current_revision is None:
            raise RuntimeError("Database revision is missing after migration.")
        head_revision = get_head_revision()
        if current_revision != head_revision:
            raise RuntimeError(
                "Database migration did not reach Alembic head revision: "
                f"current={current_revision}, head={head_revision}"
            )

        return MigrationResult(
            database_url=resolved_database_url,
            previous_revision=previous_revision,
            current_revision=current_revision,
            head_revision=head_revision,
            backup_path=backup_path,
        )
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run safe DB migration with optional backup."
    )
    parser.add_argument(
        "--database-url", help="Override DATABASE_URL for this run.", default=None
    )
    parser.add_argument(
        "--backup-dir", help="Directory for migration backups.", default=None
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip pre-migration sqlite backup.",
    )
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None
    result = migrate_database(
        database_url=args.database_url,
        backup_dir=backup_dir,
        skip_backup=args.skip_backup,
    )

    if result.backup_path is not None:
        print(f"Pre-migration backup: {result.backup_path}")
    print(
        "Migration complete: "
        f"previous={result.previous_revision}, current={result.current_revision}"
    )


if __name__ == "__main__":
    main()
