from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _ensure_column(engine: Engine, table_name: str, column_name: str, ddl: str) -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_columns = {
            column_info["name"] for column_info in inspector.get_columns(table_name)
        }
        if column_name not in existing_columns:
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")
            )


def _ensure_index(engine: Engine, index_name: str, table_name: str, column_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE INDEX IF NOT EXISTS {index_name} "
                f"ON {table_name} ({column_name})"
            )
        )


def run_startup_migrations(engine: Engine) -> None:
    _ensure_column(engine, "documents", "user_id", "VARCHAR")
    _ensure_column(engine, "blocks", "user_id", "VARCHAR")
    _ensure_column(engine, "task_cache", "user_id", "VARCHAR")
    _ensure_column(engine, "ai_provider_settings", "user_id", "VARCHAR")
    _ensure_column(engine, "silent_analysis_jobs", "user_id", "VARCHAR")

    _ensure_index(engine, "ix_documents_user_id", "documents", "user_id")
    _ensure_index(engine, "ix_blocks_user_id", "blocks", "user_id")
    _ensure_index(engine, "ix_task_cache_user_id", "task_cache", "user_id")
    _ensure_index(
        engine, "ix_ai_provider_settings_user_id", "ai_provider_settings", "user_id"
    )
    _ensure_index(
        engine, "ix_silent_analysis_jobs_user_id", "silent_analysis_jobs", "user_id"
    )
