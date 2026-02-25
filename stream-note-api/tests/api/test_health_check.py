import asyncio

import pytest
from fastapi import HTTPException

from app.main import health_check


class FakeConnection:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.executed_statements: list[str] = []

    def execute(self, statement: object) -> None:
        self.executed_statements.append(str(statement))
        if self.should_fail:
            raise RuntimeError("database down")


class _ConnectionContext:
    def __init__(self, connection: FakeConnection) -> None:
        self._connection = connection

    def __enter__(self) -> FakeConnection:
        return self._connection

    def __exit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False


class FakeEngine:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.connection = FakeConnection(should_fail=should_fail)

    def connect(self) -> _ConnectionContext:
        return _ConnectionContext(self.connection)


def test_health_check_returns_revision_and_connectivity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_engine = FakeEngine()
    monkeypatch.setattr("app.main.engine", fake_engine)
    monkeypatch.setattr(
        "app.main.get_current_database_revision", lambda _engine: "rev-1"
    )
    monkeypatch.setattr("app.main.get_head_revision", lambda: "rev-1")

    result = asyncio.run(health_check())

    assert result == {
        "status": "ok",
        "db_connection": "ok",
        "db_revision": "rev-1",
        "db_head_revision": "rev-1",
    }
    assert fake_engine.connection.executed_statements == ["SELECT 1"]


def test_health_check_returns_503_when_database_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_engine = FakeEngine(should_fail=True)
    monkeypatch.setattr("app.main.engine", fake_engine)

    with pytest.raises(HTTPException) as error_info:
        asyncio.run(health_check())

    error = error_info.value
    assert error.status_code == 503
    assert error.detail == "Database is unavailable"
    assert fake_engine.connection.executed_statements == ["SELECT 1"]


def test_health_check_returns_503_when_revision_query_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_engine = FakeEngine()
    monkeypatch.setattr("app.main.engine", fake_engine)

    def _raise_revision_error(_engine):
        raise RuntimeError("revision lookup failed")

    monkeypatch.setattr("app.main.get_current_database_revision", _raise_revision_error)

    with pytest.raises(HTTPException) as error_info:
        asyncio.run(health_check())

    error = error_info.value
    assert error.status_code == 503
    assert error.detail == "Database is unavailable"
    assert fake_engine.connection.executed_statements == ["SELECT 1"]
