"""OpenAI-compatible LLM client supporting Tool Calling (ReAct) and structured JSON mode."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

import requests

from agent_runtime.config import LLMConfig


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


def _strip_markdown_fences(raw_text: str) -> str:
    """Strip optional ```json ... ``` markdown code fences around JSON output."""
    text = raw_text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


class LLMClient:
    """Single entry point for OpenAI-compatible Chat Completions (tools & JSON output)."""

    def __init__(
        self,
        config: LLMConfig,
        transport: Callable[[str, dict[str, str], dict[str, Any], int], tuple[int, str]] | None = None,
    ) -> None:
        self._config = config
        self._transport = transport

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
        if self._transport is not None:
            status_code, text_body = self._transport(
                url, headers, payload, self._config.timeout_seconds
            )
        else:
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._config.timeout_seconds,
                )
                status_code = resp.status_code
                text_body = resp.text
            except requests.RequestException as exc:
                raise LLMError(f"LLM HTTP request failed: {exc}") from exc

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
                    args_dict = json.loads(raw_args) if raw_args.strip() else {}
                except json.JSONDecodeError as exc:
                    raise LLMError(
                        f"Invalid JSON in tool call arguments for {name}: {raw_args}"
                    ) from exc
            elif isinstance(raw_args, dict):
                args_dict = raw_args
            else:
                raise LLMError(f"Unexpected tool call arguments type: {type(raw_args)}")

            parsed_calls.append(
                ToolCall(
                    id=tc.get("id") or f"call_{idx}",
                    name=name,
                    arguments=args_dict,
                )
            )
        return LLMResponse(content=content, tool_calls=parsed_calls)

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        required_keys: tuple[str, ...] = (),
        model: str | None = None,
    ) -> dict[str, Any]:
        """Invoke LLM expecting a JSON object response and validate required keys."""
        payload: dict[str, Any] = {
            "model": model or self._config.evaluator_model or self._config.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": self._config.temperature,
        }
        data = self._post_completions(payload)
        message = data["choices"][0].get("message", {})
        raw_content = message.get("content") or ""
        cleaned = _strip_markdown_fences(raw_content)
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
