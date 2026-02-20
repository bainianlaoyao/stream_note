import pytest

from app.services.ai_service import AIProviderConfig, AIService


def test_parse_tasks_response_with_json_array() -> None:
    content = '[{"text":"明天下午去打游戏","has_time":true,"time_expr":"明天下午"}]'
    tasks = AIService._parse_tasks_response(content)
    assert len(tasks) == 1
    assert tasks[0]["text"] == "明天下午去打游戏"
    assert tasks[0]["time_expr"] == "明天下午"
    assert tasks[0]["has_time"] is True


def test_parse_tasks_response_with_fenced_json() -> None:
    content = """```json
[
  {"text": "明天下午要做饭", "time_expr": "明天下午"}
]
```"""
    tasks = AIService._parse_tasks_response(content)
    assert len(tasks) == 1
    assert tasks[0]["text"] == "明天下午要做饭"
    assert tasks[0]["time_expr"] == "明天下午"
    assert tasks[0]["has_time"] is True


def test_parse_tasks_response_with_tasks_object() -> None:
    content = '{"tasks":[{"text":"看 红苹果","has_time":false,"time_expr":null}]}'
    tasks = AIService._parse_tasks_response(content)
    assert len(tasks) == 1
    assert tasks[0]["text"] == "看 红苹果"
    assert tasks[0]["time_expr"] is None
    assert tasks[0]["has_time"] is False


def test_parse_tasks_response_invalid_content_returns_empty_list() -> None:
    tasks = AIService._parse_tasks_response("not a json response")
    assert tasks == []


def test_provider_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_PROVIDER", "siliconflow")
    monkeypatch.setenv("OPENAI_API_BASE", "https://api.example.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    monkeypatch.setenv("OPENAI_MODEL", "model-x")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "18.5")
    monkeypatch.setenv("OPENAI_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("OPENAI_DISABLE_THINKING", "0")

    config = AIProviderConfig.from_env()

    assert config.provider == "siliconflow"
    assert config.api_base == "https://api.example.com/v1"
    assert config.api_key == "secret-key"
    assert config.model == "model-x"
    assert config.timeout_seconds == 18.5
    assert config.max_attempts == 3
    assert config.disable_thinking is False


def test_build_extra_body_only_for_siliconflow() -> None:
    siliconflow_service = AIService(
        config=AIProviderConfig(
            provider="siliconflow",
            api_base="http://localhost:11434/v1",
            api_key="dummy-key",
            model="llama3.2",
            timeout_seconds=20.0,
            max_attempts=2,
            disable_thinking=True,
        )
    )
    openai_service = AIService(
        config=AIProviderConfig(
            provider="openai",
            api_base="https://api.openai.com/v1",
            api_key="sk-test",
            model="gpt-4o-mini",
            timeout_seconds=20.0,
            max_attempts=2,
            disable_thinking=True,
        )
    )

    assert siliconflow_service._build_extra_body() == {"enable_thinking": False}
    assert openai_service._build_extra_body() is None
