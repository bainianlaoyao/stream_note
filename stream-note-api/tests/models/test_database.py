import pytest

from app.models.database import _is_sqlite_url, get_db


class FakeSession:
    def __init__(self) -> None:
        self.rollback_calls = 0
        self.close_calls = 0

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def test_get_db_closes_session_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr("app.models.database.SessionLocal", lambda: session)

    generator = get_db()
    assert next(generator) is session

    with pytest.raises(StopIteration):
        next(generator)

    assert session.rollback_calls == 0
    assert session.close_calls == 1


def test_get_db_rolls_back_and_closes_session_on_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr("app.models.database.SessionLocal", lambda: session)

    generator = get_db()
    assert next(generator) is session

    with pytest.raises(RuntimeError, match="boom"):
        generator.throw(RuntimeError("boom"))

    assert session.rollback_calls == 1
    assert session.close_calls == 1


def test_is_sqlite_url_uses_backend_name_parsing() -> None:
    assert _is_sqlite_url("sqlite:///./stream_note.db") is True
    assert _is_sqlite_url("sqlite+pysqlite:///./stream_note.db") is True
    assert _is_sqlite_url("postgresql+psycopg://user:pass@localhost/db") is False
