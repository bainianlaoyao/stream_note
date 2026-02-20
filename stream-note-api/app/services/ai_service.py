import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.core.env import load_env_file

SUPPORTED_AI_PROVIDERS = {"openai_compatible", "openai", "ollama", "siliconflow"}
FENCED_JSON_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AIServiceError(Exception):
    pass


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    api_base: str
    api_key: str
    model: str
    timeout_seconds: float
    max_attempts: int
    disable_thinking: bool

    @classmethod
    def from_env(cls) -> "AIProviderConfig":
        load_env_file()
        provider = cls._normalize_provider(os.getenv("OPENAI_PROVIDER", "openai_compatible"))
        api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
        api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
        model = os.getenv("OPENAI_MODEL", "llama3.2")
        timeout_seconds = cls._parse_float_env("OPENAI_TIMEOUT_SECONDS", 20.0)
        max_attempts = max(1, cls._parse_int_env("OPENAI_MAX_ATTEMPTS", 2))
        disable_thinking = _is_truthy(os.getenv("OPENAI_DISABLE_THINKING", "1"))
        return cls(
            provider=provider,
            api_base=api_base,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_attempts=max_attempts,
            disable_thinking=disable_thinking,
        )

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized in SUPPORTED_AI_PROVIDERS:
            return normalized
        return "openai_compatible"

    @staticmethod
    def _parse_float_env(key: str, default: float) -> float:
        raw_value = os.getenv(key)
        if raw_value is None:
            return default
        try:
            return float(raw_value)
        except ValueError:
            return default

    @staticmethod
    def _parse_int_env(key: str, default: int) -> int:
        raw_value = os.getenv(key)
        if raw_value is None:
            return default
        try:
            return int(raw_value)
        except ValueError:
            return default


class AIService:
    def __init__(self, config: Optional[AIProviderConfig] = None):
        resolved_config = config if config is not None else AIProviderConfig.from_env()
        self.provider = resolved_config.provider
        self.model = resolved_config.model
        self.max_attempts = max(1, resolved_config.max_attempts)
        self.disable_thinking = resolved_config.disable_thinking

        self.client = OpenAI(
            base_url=resolved_config.api_base,
            api_key=resolved_config.api_key,
            timeout=resolved_config.timeout_seconds,
            max_retries=0,
        )

    def extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        system_prompt = """You are a task extraction assistant for short notes.
Use semantic understanding, not keyword matching.
The notes come from a to-do oriented personal knowledge app.

Definition of actionable task:
- A concrete action that can be executed (including implicit imperative or plan statements).
- If the text is only preference, emotion, description, or fact, return no task.
- If the text is a short verb-object phrase from personal notes, treat it as actionable by default.
- In ambiguous cases, prefer recall for actionable intent over precision.

Output requirements:
- Return JSON array only (no markdown, no explanation).
- Never output reasoning traces or <think> blocks.
- Each item must be:
  {"text":"task description","has_time":true|false,"time_expr":"raw time phrase or null"}
- Keep "text" concise while preserving intent.
- For short single-line notes, prefer verbatim copy of the actionable phrase (only trim redundant spaces).
- Prefer copying wording from the original note; do not paraphrase unless necessary.
- Do not compress the task text by dropping helper words from the original action phrase.
- Do not add new punctuation, quotes, or title formatting that is not present in the note.
- If note uses an action-detail separator (for example ":" / "：" / "-"), keep it in "text" when it carries intent.
- "time_expr" must be copied from the original text when present.
"""

        user_prompt = f"Note block: {text}"

        request_kwargs = self._build_request_kwargs(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

        response = self._request_with_retries(request_kwargs)
        content = response.choices[0].message.content
        if content is None:
            return []
        return self._parse_tasks_response(content)

    def test_connection(self) -> Dict[str, Any]:
        request_kwargs = self._build_request_kwargs(
            messages=[
                {"role": "system", "content": "You are a connectivity probe."},
                {"role": "user", "content": "Reply with OK."},
            ],
            temperature=0.0,
            max_tokens=12,
        )

        started_at = time.perf_counter()
        response = self._request_with_retries(request_kwargs)
        latency_ms = int((time.perf_counter() - started_at) * 1000)

        content = response.choices[0].message.content
        if content is None or content.strip() == "":
            raise AIServiceError("LLM request succeeded but returned empty response")

        return {"latency_ms": latency_ms, "message": content.strip()}

    def _request_with_retries(self, request_kwargs: Dict[str, Any]) -> Any:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self.client.chat.completions.create(**request_kwargs)
            except (APITimeoutError, APIConnectionError, APIStatusError) as error:
                last_error = error
                is_retryable = self._is_retryable(error)
                if attempt < self.max_attempts and is_retryable:
                    time.sleep(0.4 * attempt)
                    continue
                break
            except Exception as error:
                last_error = error
                break

        assert last_error is not None
        raise AIServiceError(f"LLM request failed: {last_error}") from last_error

    def _build_request_kwargs(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        extra_body = self._build_extra_body()
        if extra_body is not None:
            request_kwargs["extra_body"] = extra_body

        return request_kwargs

    def _build_extra_body(self) -> Optional[Dict[str, Any]]:
        # SiliconFlow supports this flag to control reasoning mode.
        if self.provider == "siliconflow":
            return {"enable_thinking": not self.disable_thinking}
        return None

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        if isinstance(error, (APITimeoutError, APIConnectionError)):
            return True
        if isinstance(error, APIStatusError):
            return error.status_code in (429, 500, 502, 503, 504)
        return False

    @staticmethod
    def _parse_tasks_response(content: str) -> List[Dict[str, Any]]:
        for candidate in AIService._json_candidates(content):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            normalized = AIService._normalize_payload(parsed)
            if normalized is not None:
                return normalized

        return []

    @staticmethod
    def _json_candidates(content: str) -> List[str]:
        stripped = content.strip()
        candidates: List[str] = [stripped] if stripped else []

        for fenced in FENCED_JSON_PATTERN.findall(stripped):
            candidate = fenced.strip()
            if candidate:
                candidates.append(candidate)

        array_match = ARRAY_PATTERN.search(stripped)
        if array_match:
            candidates.append(array_match.group(0).strip())

        deduped: List[str] = []
        for candidate in candidates:
            if candidate not in deduped:
                deduped.append(candidate)
        return deduped

    @staticmethod
    def _normalize_payload(payload: Any) -> Optional[List[Dict[str, Any]]]:
        if isinstance(payload, list):
            return AIService._normalize_task_list(payload)

        if isinstance(payload, dict):
            tasks_field = payload.get("tasks")
            if isinstance(tasks_field, list):
                return AIService._normalize_task_list(tasks_field)

        return None

    @staticmethod
    def _normalize_task_list(raw_tasks: List[Any]) -> List[Dict[str, Any]]:
        normalized_tasks: List[Dict[str, Any]] = []
        for item in raw_tasks:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text", "")).strip()
            if text == "":
                continue

            raw_time_expr = item.get("time_expr")
            time_expr = str(raw_time_expr).strip() if raw_time_expr else None
            has_time = bool(item.get("has_time")) if "has_time" in item else time_expr is not None
            normalized_tasks.append(
                {
                    "text": text,
                    "has_time": has_time,
                    "time_expr": time_expr,
                }
            )

        return normalized_tasks
