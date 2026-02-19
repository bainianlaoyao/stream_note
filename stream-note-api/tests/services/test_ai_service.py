from app.services.ai_service import AIService


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
