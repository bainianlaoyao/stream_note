import sqlite3
from typing import Any, Dict

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.api.v1.endpoints.ai import reset_debug_state
from app.models.block import Block
from app.models.task import TaskCache


class DummyUser:
    def __init__(self, user_id: str):
        self.id = user_id


def make_sqlite_locked_error() -> OperationalError:
    return OperationalError(
        statement="DELETE FROM task_cache",
        params={},
        orig=sqlite3.OperationalError("database is locked"),
    )


class FakeQuery:
    def __init__(self, session: "FakeSession", model: Any):
        self.session = session
        self.model = model

    def filter(self, *args: Any, **kwargs: Any) -> "FakeQuery":
        del args, kwargs
        return self

    def delete(self, synchronize_session: bool = False) -> int:
        del synchronize_session
        if self.model is TaskCache:
            self.session.delete_calls += 1
            if self.session.fail_delete_attempts > 0:
                self.session.fail_delete_attempts -= 1
                raise make_sqlite_locked_error()
            return self.session.delete_result
        return 0

    def update(
        self, values: Dict[Any, Any], synchronize_session: bool = False
    ) -> int:
        del values, synchronize_session
        if self.model is Block:
            self.session.update_calls += 1
            return self.session.update_result
        return 0


class FakeSession:
    def __init__(
        self,
        fail_delete_attempts: int,
        delete_result: int = 2,
        update_result: int = 3,
    ):
        self.fail_delete_attempts = fail_delete_attempts
        self.delete_result = delete_result
        self.update_result = update_result
        self.rollback_calls = 0
        self.commit_calls = 0
        self.delete_calls = 0
        self.update_calls = 0

    def query(self, model: Any) -> FakeQuery:
        return FakeQuery(self, model)

    def rollback(self) -> None:
        self.rollback_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1


def test_reset_debug_state_retries_on_sqlite_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr("app.api.v1.endpoints.ai.time.sleep", fake_sleep)
    db = FakeSession(fail_delete_attempts=2, delete_result=7, update_result=11)

    result = reset_debug_state(
        db=db,  # type: ignore[arg-type]
        current_user=DummyUser("user-1"),  # type: ignore[arg-type]
    )

    assert result.deleted_tasks == 7
    assert result.reset_blocks == 11
    assert db.rollback_calls == 2
    assert db.commit_calls == 1
    assert db.delete_calls == 3
    assert db.update_calls == 1
    assert sleep_calls == [0.2, 0.4]


def test_reset_debug_state_returns_503_after_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.ai.time.sleep", lambda _seconds: None)
    db = FakeSession(fail_delete_attempts=5)

    with pytest.raises(HTTPException) as error_info:
        reset_debug_state(
            db=db,  # type: ignore[arg-type]
            current_user=DummyUser("user-1"),  # type: ignore[arg-type]
        )

    error = error_info.value
    assert error.status_code == 503
    assert error.detail == "Database is busy. Please retry in a moment."
    assert db.rollback_calls == 3
    assert db.commit_calls == 0
    assert db.delete_calls == 3
    assert db.update_calls == 0
