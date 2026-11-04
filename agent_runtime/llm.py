"""OpenAI-compatible LLM client supporting Tool Calling (ReAct) and structured JSON mode."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests

from agent_runtime.config import LLMConfig

TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """Raised when LLM API request or structured output parsing fails."""


@dataclass(frozen=True)
class ToolCall:
    """Parsed tool invocation requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    """Structured response from chat_with_tools."""

    content: str
    tool_calls: list[ToolCall]


def _extract_json_object(raw_text: str) -> str:
    """Extract a JSON object string from raw LLM output (including prose + markdown fences)."""
    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return text


class LLMClient:
    """Single entry point for OpenAI-compatible Chat Completions (tools & JSON output)."""

    def __init__(
        self,
        config: LLMConfig,
        transport: Callable[[str, dict[str, str], dict[str, Any], int], tuple[int, str]] | None = None,
        max_retries: int = 3,
    ) -> None:
        self._config = config
        self._transport = transport
        self._max_retries = max(1, int(max_retries))

    @property
    def config(self) -> LLMConfig:
        return self._config

    def _post_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._config.api_key:
            raise LLMError("LLM_API_KEY is not configured")
        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        req_payload = dict(payload)
        model_name = str(req_payload.get("model", "")).lower()
        if "deepseek-flash" in model_name and "reasoning_effort" not in req_payload:
            req_payload["reasoning_effort"] = "low"

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            if self._transport is not None:
                status_code, text_body = self._transport(
                    url, headers, req_payload, self._config.timeout_seconds
                )
            else:
                try:
                    resp = requests.post(
                        url,
                        headers=headers,
                        json=req_payload,
                        timeout=self._config.timeout_seconds,
                    )
                    status_code = resp.status_code
                    text_body = resp.text
                except requests.RequestException as exc:
                    last_err = exc
                    if attempt + 1 < self._max_retries:
                        time.sleep(0.2 * (2**attempt))
                        continue
                    raise LLMError(f"LLM HTTP request failed: {exc}") from exc

            if status_code in TRANSIENT_HTTP_STATUSES and attempt + 1 < self._max_retries:
                if self._transport is None:
                    time.sleep(0.2 * (2**attempt))
                continue

            if status_code != 200:
                raise LLMError(
                    f"LLM API returned HTTP {status_code}: {text_body[:300]}"
                )
            try:
                data = json.loads(text_body)
            except ValueError as exc:
                raise LLMError(f"Invalid JSON from LLM endpoint: {exc}") from exc

            if not isinstance(data, dict) or not data.get("choices"):
                raise LLMError(f"Malformed LLM completion response: {data}")
            return data

        raise LLMError(f"LLM request exhausted retries: {last_err}")

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str = "auto",
        model: str | None = None,
    ) -> LLMResponse:
        """Invoke LLM with OpenAI tool schemas and parse assistant content + tool_calls."""
        payload: dict[str, Any] = {
            "model": model or self._config.client_model or self._config.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": self._config.temperature,
        }
        data = self._post_completions(payload)
        message = data["choices"][0].get("message", {})
        content = message.get("content") or ""
        raw_tool_calls = message.get("tool_calls") or []

        parsed_calls: list[ToolCall] = []
        for idx, tc in enumerate(raw_tool_calls):
            fn = tc.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            if isinstance(raw_args, str):
                try:
                    parsed_obj = json.loads(raw_args) if raw_args.strip() else {}
                    args_dict = (
                        parsed_obj
                        if isinstance(parsed_obj, dict)
                        else {"__malformed_raw__": raw_args}
                    )
                except json.JSONDecodeError:
                    try:
                        repaired_obj = json.loads(_extract_json_object(raw_args))
                        args_dict = (
                            repaired_obj
                            if isinstance(repaired_obj, dict)
                            else {"__malformed_raw__": raw_args}
                        )
                    except (json.JSONDecodeError, ValueError):
                        args_dict = {"__malformed_raw__": raw_args}
            elif isinstance(raw_args, dict):
                args_dict = raw_args
            else:
                args_dict = {"__malformed_raw__": str(raw_args)}

            parsed_calls.append(
                ToolCall(
                    id=tc.get("id") or f"call_{idx}",
                    name=name,
                    arguments=args_dict,
                )
            )
        return LLMResponse(content=content, tool_calls=parsed_calls)

    def _parse_and_validate_json(
        self, raw_content: str, required_keys: tuple[str, ...]
    ) -> dict[str, Any]:
        cleaned = _extract_json_object(raw_content)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM did not return valid JSON: {raw_content}") from exc

        if not isinstance(parsed, dict):
            raise LLMError(f"Expected JSON object from LLM, got {type(parsed).__name__}")

        for key in required_keys:
            if key not in parsed:
                raise LLMError(f"LLM JSON response missing required key '{key}': {parsed}")
        return parsed

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        required_keys: tuple[str, ...] = (),
        model: str | None = None,
    ) -> dict[str, Any]:
        """Invoke LLM expecting a JSON object response and validate required keys (with 1 repair retry)."""
        target_model = model or self._config.evaluator_model or self._config.model
        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": self._config.temperature,
        }
        data = self._post_completions(payload)
        message = data["choices"][0].get("message", {})
        raw_content = message.get("content") or ""
        try:
            return self._parse_and_validate_json(raw_content, required_keys)
        except LLMError:
            repair_messages = list(messages) + [
                {"role": "assistant", "content": raw_content},
                {
                    "role": "user",
                    "content": (
                        "Your previous output was malformed JSON or missing required keys "
                        f"{list(required_keys)}. Respond ONLY with a valid JSON object."
                    ),
                },
            ]
            repair_payload: dict[str, Any] = {
                "model": target_model,
                "messages": repair_messages,
                "response_format": {"type": "json_object"},
                "temperature": self._config.temperature,
            }
            repair_data = self._post_completions(repair_payload)
            repair_msg = repair_data["choices"][0].get("message", {})
            repair_content = repair_msg.get("content") or ""
            return self._parse_and_validate_json(repair_content, required_keys)
