import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

FENCED_JSON_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")


class AIService:
    def __init__(self):
        api_base = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
        api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
        self.model = os.getenv("OPENAI_MODEL", "llama3.2")
        timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key,
            timeout=timeout,
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
- Each item must be:
  {"text":"task description","has_time":true|false,"time_expr":"raw time phrase or null"}
- Keep "text" concise while preserving intent.
- "time_expr" must be copied from the original text when present.
"""

        user_prompt = f"Note block: {text}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )

            content = response.choices[0].message.content
            if content is None:
                return []
            return self._parse_tasks_response(content)
        except Exception as e:
            print(f"AI extraction error: {e}")
            return []

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
