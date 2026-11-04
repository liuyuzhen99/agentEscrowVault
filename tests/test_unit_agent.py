"""Unit tests for AgentEscrowVault Python LLM Agent Runtime (Tasks 3, 4, 5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agent_runtime.config import AgentRuntimeConfig, LLMConfig, load_config
from agent_runtime.llm import LLMClient, LLMError, LLMResponse, ToolCall
from agent_runtime.x402 import decode_x402_header, encode_x402_header, fetch_deliverable, probe_quote
from agent_runtime.tools import TOOL_SCHEMAS, AgentToolbox
from agent_runtime.evaluator import EvaluatorAgent
from agent_runtime.provider import ProviderAgent
from agent_runtime.client_agent import ClientAgent


# ============================================================================
# Task 3 Tests: LLM Config, LLMClient, 402 Probe, and 6 Agent Tools
# ============================================================================


def test_llm_config_and_client(tmp_path: Path) -> None:
    """Verify LLMConfig loads from .env / env vars and LLMClient handles tool_calls & chat_json."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_API_KEY=sk-test-key-123\n"
        "LLM_BASE_URL=https://llm.example.com/v1\n"
        "LLM_MODEL=deepseek-chat\n"
        "CLIENT_LLM_MODEL=gpt-4o\n"
        "EVALUATOR_LLM_MODEL=claude-3-5-sonnet\n"
        "LLM_TEMPERATURE=0.2\n"
        "RPC_URL=http://127.0.0.1:8545\n"
        "CHAIN_ID=84532\n",
        encoding="utf-8",
    )

    cfg = load_config(env_path=env_file, environ={})
    assert isinstance(cfg, AgentRuntimeConfig)
    assert isinstance(cfg.llm, LLMConfig)
    assert cfg.llm.api_key == "sk-test-key-123"
    assert cfg.llm.base_url == "https://llm.example.com/v1"
    assert cfg.llm.model == "deepseek-chat"
    assert cfg.llm.client_model == "gpt-4o"
    assert cfg.llm.evaluator_model == "claude-3-5-sonnet"
    assert cfg.llm.temperature == 0.2
    assert cfg.rpc_url == "http://127.0.0.1:8545"
    assert cfg.chain_id == 84532

    # Verify LLMClient.chat_with_tools and chat_json using in-process HTTP transport
    captured_requests: list[dict[str, Any]] = []

    def fake_openai_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        captured_requests.append(
            {
                "url": url,
                "auth": headers.get("Authorization"),
                "body": body,
                "timeout": timeout,
            }
        )
        if body.get("tools"):
            resp = {
                "id": "chatcmpl-1",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Checking vault status first.",
                            "tool_calls": [
                                {
                                    "id": "call_abc123",
                                    "type": "function",
                                    "function": {
                                        "name": "get_vault_status",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        }
                    }
                ],
            }
        else:
            # Return markdown-fenced JSON to verify stripping & schema validation
            resp = {
                "id": "chatcmpl-2",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": '```json\n{"verdict": "PASS", "score": 92, "reasons": ["All 30 addresses verified"]}\n```',
                        }
                    }
                ],
            }
        return 200, json.dumps(resp)

    llm_cfg = LLMConfig(
        api_key="sk-live-secret",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        client_model="gpt-4o-mini",
        evaluator_model="gpt-4o-mini",
        temperature=0.0,
        timeout_seconds=10,
    )
    client = LLMClient(llm_cfg, transport=fake_openai_transport)

    tool_resp: LLMResponse = client.chat_with_tools(
        messages=[{"role": "user", "content": "Buy gas data"}],
        tools=TOOL_SCHEMAS,
    )
    assert tool_resp.content == "Checking vault status first."
    assert len(tool_resp.tool_calls) == 1
    assert tool_resp.tool_calls[0] == ToolCall(
        id="call_abc123",
        name="get_vault_status",
        arguments={},
    )
    assert captured_requests[0]["auth"] == "Bearer sk-live-secret"
    assert captured_requests[0]["url"] == "https://api.openai.com/v1/chat/completions"

    json_resp = client.chat_json(
        messages=[{"role": "user", "content": "Judge this report"}],
        required_keys=("verdict", "score", "reasons"),
    )
    assert json_resp == {
        "verdict": "PASS",
        "score": 92,
        "reasons": ["All 30 addresses verified"],
    }

    # Verify LLMError is raised on missing API key or invalid JSON
    empty_key_client = LLMClient(
        LLMConfig(
            api_key="",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            client_model="gpt-4o-mini",
            evaluator_model="gpt-4o-mini",
            temperature=0.0,
            timeout_seconds=5,
        ),
        transport=fake_openai_transport,
    )
    with pytest.raises(LLMError, match="LLM_API_KEY"):
        empty_key_client.chat_with_tools(messages=[], tools=TOOL_SCHEMAS)


def test_probe_quote() -> None:
    """Verify 402 Payment Required header encoding, decoding, and HTTP probe_quote."""
    requirement = {
        "price_usd": 0.003,
        "pay_to": "0x1111111111111111111111111111111111111111",
        "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "type": "direct",
        "network": "eip155:84532",
        "description": "Real-time Base gas feed",
    }
    encoded = encode_x402_header(requirement)
    decoded = decode_x402_header(encoded)
    assert decoded["price_usd"] == 0.003
    assert decoded["pay_to"] == "0x1111111111111111111111111111111111111111"
    assert decoded["asset"] == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    assert decoded["type"] == "direct"

    def fake_402_get(url: str, timeout: int) -> tuple[int, dict[str, str], str]:
        return 402, {"X-Payment-Required": encoded}, '{"error": "Payment Required"}'

    quote = probe_quote("http://merchant.local/api/gas", http_get=fake_402_get)
    assert quote["status_code"] == 402
    assert quote["price_usd"] == 0.003
    assert quote["pay_to"] == "0x1111111111111111111111111111111111111111"
    assert quote["asset"] == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    assert quote["type"] == "direct"

    # Case-insensitive header key support (e.g. uppercase PAYMENT-REQUIRED from HTTP servers)
    quote_upper = probe_quote(
        "http://merchant.local/api/gas-upper",
        http_get=lambda u, t: (402, {"PAYMENT-REQUIRED": encoded}, "Payment Required"),
    )
    assert quote_upper["status_code"] == 402
    assert quote_upper["price_usd"] == 0.003
    assert quote_upper["pay_to"] == "0x1111111111111111111111111111111111111111"

    # Also verify non-402 handling and invalid header handling
    non_402 = probe_quote(
        "http://merchant.local/api/free",
        http_get=lambda u, t: (200, {}, "ok"),
    )
    assert non_402["status_code"] == 200
    assert "Expected HTTP 402" in non_402["error"]

    with pytest.raises(ValueError, match="Invalid Base64"):
        decode_x402_header("!!!not_base64!!!")


def test_vault_tools() -> None:
    """Verify all 6 TOOL_SCHEMAS and AgentToolbox dispatch including structured error observation."""
    tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]
    assert tool_names == [
        "probe_quote",
        "get_vault_status",
        "pay_direct",
        "hire_escrow_job",
        "inspect_job",
        "finish_task",
    ]

    class StubContractManager:
        def __init__(self) -> None:
            self.direct_calls: list[tuple[str, int]] = []
            self.escrow_calls: list[tuple[str, str, int, int]] = []

        def get_vault_status(self, candidate_payees: list[str] | None = None) -> dict[str, Any]:
            return {
                "vault_balance_usd": 0.10,
                "max_per_tx_direct_usd": 0.01,
                "max_per_tx_escrow_usd": 0.06,
                "max_daily_spend_usd": 0.10,
                "daily_spend_counter_usd": 0.0,
                "remaining_daily_budget_usd": 0.10,
                "paused": False,
                "whitelisted_payees": ["0x1111111111111111111111111111111111111111"],
            }

        def spend_direct(self, payee_address: str, amount_raw: int) -> dict[str, Any]:
            if amount_raw > 10_000:
                raise RuntimeError("ExceedsPerTxDirectCap(50000, 10000)")
            self.direct_calls.append((payee_address, amount_raw))
            return {"tx_hash": "0xdirect123", "amount_raw": amount_raw}

        def fund_job(
            self,
            provider_address: str,
            evaluator_address: str,
            amount_raw: int,
            duration_seconds: int,
        ) -> dict[str, Any]:
            self.escrow_calls.append((provider_address, evaluator_address, amount_raw, duration_seconds))
            return {"tx_hash": "0xescrow456", "job_id": 1, "amount_raw": amount_raw, "deadline": 1700003600}

        def get_job(self, job_id: int) -> dict[str, Any]:
            return {
                "job_id": job_id,
                "client": "0xVault",
                "provider": "0xProviderA",
                "evaluator": "0xEval",
                "amount_usd": 0.05,
                "deadline": 1700003600,
                "result_hash": "0x" + "ab" * 32,
                "state": "Submitted",
                "state_code": 2,
            }

    cm = StubContractManager()
    toolbox = AgentToolbox(contract_manager=cm)  # type: ignore[arg-type]

    status_res = toolbox.execute_tool("get_vault_status", {})
    assert status_res["ok"] is True
    assert status_res["max_per_tx_direct_usd"] == 0.01
    assert status_res["whitelisted_payees"] == ["0x1111111111111111111111111111111111111111"]

    # Over-cap direct payment should return a structured error observation for the LLM to reflect on
    over_cap = toolbox.execute_tool(
        "pay_direct",
        {
            "payee_address": "0x1111111111111111111111111111111111111111",
            "amount_usd": 0.05,
            "reason": "Try direct pay for deep report",
        },
    )
    assert over_cap["ok"] is False
    assert "ExceedsPerTxDirectCap" in over_cap["error"]

    # Valid direct payment
    ok_direct = toolbox.execute_tool(
        "pay_direct",
        {
            "payee_address": "0x1111111111111111111111111111111111111111",
            "amount_usd": 0.005,
            "reason": "Gas price feed",
        },
    )
    assert ok_direct["ok"] is True
    assert ok_direct["tx_hash"] == "0xdirect123"
    assert cm.direct_calls == [("0x1111111111111111111111111111111111111111", 5_000)]

    # Hire escrow job
    escrow_res = toolbox.execute_tool(
        "hire_escrow_job",
        {
            "provider_address": "0x2222222222222222222222222222222222222222",
            "evaluator_address": "0x3333333333333333333333333333333333333333",
            "amount_usd": 0.05,
            "duration_seconds": 3600,
            "task_desc": "Deep fund trace",
        },
    )
    assert escrow_res["ok"] is True
    assert escrow_res["job_id"] == 1

    # Inspect job
    inspect_res = toolbox.execute_tool("inspect_job", {"job_id": 1})
    assert inspect_res["ok"] is True
    assert inspect_res["state"] == "Submitted"

    # Finish task
    finish_res = toolbox.execute_tool("finish_task", {"final_report": "Completed fund analysis."})
    assert finish_res["ok"] is True
    assert finish_res["finished"] is True
    assert finish_res["final_report"] == "Completed fund analysis."


# ============================================================================
# Task 4 Tests: EvaluatorAgent (LLM-as-a-Judge) & ProviderAgent
# ============================================================================


def test_evaluator_judge() -> None:
    """Verify EvaluatorAgent calls LLM chat_json and executes completeJob (>=80 PASS) or rejectJob."""
    recorded_prompts: list[list[dict[str, Any]]] = []
    llm_outputs: list[dict[str, Any]] = [
        {
            "verdict": "FAIL",
            "score": 25,
            "reasons": ["Missing 30 address flows; only 2 addresses present"],
        },
        {
            "verdict": "PASS",
            "score": 95,
            "reasons": ["Contains all 30 address flows, full fields, and within 7 days"],
        },
    ]

    class FakeJudgeLLM:
        def chat_json(
            self,
            messages: list[dict[str, Any]],
            required_keys: tuple[str, ...] = ("verdict", "score", "reasons"),
            model: str | None = None,
        ) -> dict[str, Any]:
            recorded_prompts.append(messages)
            return llm_outputs.pop(0)

    class StubEscrowSettlement:
        def __init__(self) -> None:
            self.completed: list[int] = []
            self.rejected: list[tuple[int, str]] = []

        def complete_job(self, job_id: int) -> dict[str, Any]:
            self.completed.append(job_id)
            return {"tx_hash": f"0xcomplete_{job_id}", "job_id": job_id, "state": "Completed"}

        def reject_job(self, job_id: int, reason: str) -> dict[str, Any]:
            self.rejected.append((job_id, reason))
            return {"tx_hash": f"0xreject_{job_id}", "job_id": job_id, "state": "Rejected", "reason": reason}

    settlement = StubEscrowSettlement()
    evaluator = EvaluatorAgent(
        contract_manager=settlement,  # type: ignore[arg-type]
        llm_client=FakeJudgeLLM(),  # type: ignore[arg-type]
    )

    # 1st evaluation: bad deliverable -> FAIL & score 25 -> calls reject_job
    res_fail = evaluator.evaluate_and_settle(
        job_id=101,
        task_requirement="Produce token laundering penetration report",
        acceptance_criteria=["Must include 30 address flows", "Complete fields", "Within 7 days"],
        deliverable_content="Empty stub report with 2 addresses.",
    )
    assert res_fail["verdict"] == "FAIL"
    assert res_fail["score"] == 25
    assert res_fail["action"] == "rejectJob"
    assert settlement.rejected == [(101, "Missing 30 address flows; only 2 addresses present")]
    assert settlement.completed == []
    # Prompt must include task requirement, criteria, and deliverable text
    assert "30 address flows" in recorded_prompts[0][-1]["content"]
    assert "Empty stub report" in recorded_prompts[0][-1]["content"]

    # 2nd evaluation: high-quality deliverable -> PASS & score 95 -> calls complete_job
    res_pass = evaluator.evaluate_and_settle(
        job_id=102,
        task_requirement="Produce token laundering penetration report",
        acceptance_criteria=["Must include 30 address flows", "Complete fields", "Within 7 days"],
        deliverable_content="Full 30-address flow penetration analysis...",
    )
    assert res_pass["verdict"] == "PASS"
    assert res_pass["score"] == 95
    assert res_pass["action"] == "completeJob"
    assert settlement.completed == [102]


# ============================================================================
# Task 5 Tests: ClientAgent Pure LLM ReAct Loop (No hardcoded routing/reselect)
# ============================================================================


def test_client_agent_react_loop() -> None:
    """Verify ClientAgent is 100% driven by LLM tool_calls & observations across multi-turn recovery."""
    observed_messages_snapshots: list[list[dict[str, Any]]] = []

    # Simulate an LLM that decides step-by-step via tool_calls based on tool observations in messages:
    # Turn 1: get_vault_status + probe_quote(providerA) + probe_quote(providerB)
    # Turn 2: tries pay_direct(0.05) -> receives ExceedsPerTxDirectCap error in tool observation
    # Turn 3: reflects on error and calls hire_escrow_job(providerA, 0.05) -> gets job_id=1
    # Turn 4: calls inspect_job(1) -> sees state="Rejected" (fraud intercepted, funds refunded)
    # Turn 5: reflects on rejection and calls hire_escrow_job(providerB, 0.06) -> gets job_id=2
    # Turn 6: calls inspect_job(2) -> sees state="Completed" + deliverable content
    # Turn 7: calls finish_task with final synthesized report
    scripted_llm_turns: list[LLMResponse] = [
        LLMResponse(
            content="First, inspect vault limits and probe quotes from available providers.",
            tool_calls=[
                ToolCall(id="call_1", name="get_vault_status", arguments={}),
                ToolCall(
                    id="call_2",
                    name="probe_quote",
                    arguments={"resource_url": "http://provider-a.local/deep-report"},
                ),
                ToolCall(
                    id="call_3",
                    name="probe_quote",
                    arguments={"resource_url": "http://provider-b.local/deep-report"},
                ),
            ],
        ),
        LLMResponse(
            content="Attempting direct payment to Provider A for 0.05 USDC.",
            tool_calls=[
                ToolCall(
                    id="call_4",
                    name="pay_direct",
                    arguments={
                        "payee_address": "0xProviderA",
                        "amount_usd": 0.05,
                        "reason": "Buy deep report from Provider A",
                    },
                )
            ],
        ),
        LLMResponse(
            content="Direct spend failed due to ExceedsPerTxDirectCap (0.05 > 0.01). Switching to escrow with Provider A.",
            tool_calls=[
                ToolCall(
                    id="call_5",
                    name="hire_escrow_job",
                    arguments={
                        "provider_address": "0xProviderA",
                        "evaluator_address": "0xEvaluator",
                        "amount_usd": 0.05,
                        "duration_seconds": 3600,
                        "task_desc": "Deep laundering report",
                    },
                )
            ],
        ),
        LLMResponse(
            content="Checking job 1 status.",
            tool_calls=[ToolCall(id="call_6", name="inspect_job", arguments={"job_id": 1})],
        ),
        LLMResponse(
            content="Job 1 with Provider A was Rejected by Evaluator and 0.05 USDC was refunded to Vault. Switching to high-quality Provider B (0.06 USDC).",
            tool_calls=[
                ToolCall(
                    id="call_7",
                    name="hire_escrow_job",
                    arguments={
                        "provider_address": "0xProviderB",
                        "evaluator_address": "0xEvaluator",
                        "amount_usd": 0.06,
                        "duration_seconds": 3600,
                        "task_desc": "Deep laundering report (retry with Provider B)",
                    },
                )
            ],
        ),
        LLMResponse(
            content="Checking job 2 status.",
            tool_calls=[ToolCall(id="call_8", name="inspect_job", arguments={"job_id": 2})],
        ),
        LLMResponse(
            content="Job 2 completed and verified. Submitting final report.",
            tool_calls=[
                ToolCall(
                    id="call_9",
                    name="finish_task",
                    arguments={"final_report": "Verified 30-address money laundering report from Provider B."},
                )
            ],
        ),
    ]

    class SpyReActLLM:
        def chat_with_tools(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]],
            tool_choice: str = "auto",
            model: str | None = None,
        ) -> LLMResponse:
            observed_messages_snapshots.append(json.loads(json.dumps(messages)))
            return scripted_llm_turns.pop(0)

    class FakeToolbox:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            self.calls.append((name, arguments))
            if name == "get_vault_status":
                return {
                    "ok": True,
                    "vault_balance_usd": 0.10,
                    "max_per_tx_direct_usd": 0.01,
                    "max_per_tx_escrow_usd": 0.06,
                    "max_daily_spend_usd": 0.10,
                }
            if name == "probe_quote":
                url = arguments["resource_url"]
                if "provider-a" in url:
                    return {"ok": True, "price_usd": 0.05, "pay_to": "0xProviderA", "type": "escrow"}
                return {"ok": True, "price_usd": 0.06, "pay_to": "0xProviderB", "type": "escrow"}
            if name == "pay_direct":
                return {"ok": False, "error": "Contract reverted: ExceedsPerTxDirectCap(50000, 10000)"}
            if name == "hire_escrow_job":
                job_id = 1 if arguments["provider_address"] == "0xProviderA" else 2
                return {"ok": True, "job_id": job_id, "state": "Funded"}
            if name == "inspect_job":
                if arguments["job_id"] == 1:
                    return {
                        "ok": True,
                        "job_id": 1,
                        "state": "Rejected",
                        "rejection_reason": "Missing 30 address flows",
                        "refunded_to_vault": True,
                    }
                return {
                    "ok": True,
                    "job_id": 2,
                    "state": "Completed",
                    "deliverable": "Full 30-address flow report",
                }
            if name == "finish_task":
                return {"ok": True, "finished": True, "final_report": arguments["final_report"]}
            return {"ok": False, "error": f"Unknown tool {name}"}

    toolbox = FakeToolbox()
    agent = ClientAgent(
        llm_client=SpyReActLLM(),  # type: ignore[arg-type]
        toolbox=toolbox,  # type: ignore[arg-type]
        max_steps=12,
    )

    result = agent.run(
        user_goal="Produce a deep laundering and fund penetration report within 0.1 USDC budget.",
        market_resources=[
            "http://provider-a.local/deep-report",
            "http://provider-b.local/deep-report",
        ],
    )

    assert result["finished"] is True
    assert result["final_report"] == "Verified 30-address money laundering report from Provider B."
    assert [c[0] for c in toolbox.calls] == [
        "get_vault_status",
        "probe_quote",
        "probe_quote",
        "pay_direct",
        "hire_escrow_job",
        "inspect_job",
        "hire_escrow_job",
        "inspect_job",
        "finish_task",
    ]
    # Verify that tool observations (including ExceedsPerTxDirectCap and Rejected state) were fed back into LLM messages
    full_transcript = json.dumps(observed_messages_snapshots[-1])
    assert "ExceedsPerTxDirectCap" in full_transcript
    assert "Rejected" in full_transcript


def test_llm_resilience() -> None:
    """A3: Verify LLMClient handles prose-wrapped JSON, 1-step JSON repair, 429/503 retry, and malformed tool_calls JSON."""
    call_counter = {"count": 0}

    def resilient_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        call_counter["count"] += 1
        n = call_counter["count"]
        # Call 1: Transient HTTP 503 Service Unavailable -> should retry automatically
        if n == 1:
            return 503, '{"error": "Service temporarily overloaded"}'
        # Call 2: Prose + markdown fenced JSON -> should extract {"verdict": "PASS", ...}
        if n == 2:
            return 200, json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Here is my evaluation of the provider report:\n"
                                    "```json\n"
                                    '{"verdict": "PASS", "score": 88, "reasons": ["Verified 30 flows"]}\n'
                                    "```\n"
                                    "Hope this helps!"
                                ),
                            }
                        }
                    ]
                }
            )
        # Call 3: Truncated/malformed JSON on first attempt of chat_json
        if n == 3:
            return 200, json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": '{"verdict": "FAIL", "score": 15, "reasons": ["Incomplete',
                            }
                        }
                    ]
                }
            )
        # Call 4: Repair attempt succeeds with valid JSON
        if n == 4:
            return 200, json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": '{"verdict": "FAIL", "score": 15, "reasons": ["Incomplete report"]}',
                            }
                        }
                    ]
                }
            )
        # Call 5: chat_with_tools returns markdown-fenced JSON tool_calls arguments (recoverable via _extract_json_object)
        # and an unrecoverable truncated JSON tool_calls argument
        return 200, json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Calling pay_direct",
                            "tool_calls": [
                                {
                                    "id": "call_fenced_json",
                                    "type": "function",
                                    "function": {
                                        "name": "pay_direct",
                                        "arguments": (
                                            "```json\n"
                                            '{"payee_address": "0xabc", "amount_usd": 0.005, "reason": "gas"}\n'
                                            "```"
                                        ),
                                    },
                                },
                                {
                                    "id": "call_bad_json",
                                    "type": "function",
                                    "function": {
                                        "name": "pay_direct",
                                        "arguments": '{"payee_address": "0x123", "amount_usd": 0.01',
                                    },
                                },
                            ],
                        }
                    }
                ]
            }
        )

    cfg = LLMConfig(
        api_key="sk-resilience",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-flash",
        client_model="deepseek-flash",
        evaluator_model="deepseek-flash",
        temperature=0.0,
        timeout_seconds=5,
    )
    client = LLMClient(cfg, transport=resilient_transport)

    # 1. Transient 503 retry + prose-wrapped JSON extraction
    res1 = client.chat_json(
        messages=[{"role": "user", "content": "Evaluate deliverable"}],
        required_keys=("verdict", "score", "reasons"),
    )
    assert res1["verdict"] == "PASS"
    assert res1["score"] == 88
    assert call_counter["count"] == 2

    # 2. Malformed JSON triggers 1-step repair retry and succeeds
    res2 = client.chat_json(
        messages=[{"role": "user", "content": "Evaluate broken deliverable"}],
        required_keys=("verdict", "score", "reasons"),
    )
    assert res2["verdict"] == "FAIL"
    assert res2["score"] == 15
    assert call_counter["count"] == 4

    # 3. Markdown-fenced tool_calls arguments JSON is recovered via _extract_json_object,
    # while unrecoverable malformed JSON is captured as __malformed_raw__ and rejected cleanly by AgentToolbox
    tool_resp = client.chat_with_tools(
        messages=[{"role": "user", "content": "Pay merchant"}],
        tools=TOOL_SCHEMAS,
    )
    assert len(tool_resp.tool_calls) == 2
    assert tool_resp.tool_calls[0].arguments == {
        "payee_address": "0xabc",
        "amount_usd": 0.005,
        "reason": "gas",
    }
    assert "__malformed_raw__" in tool_resp.tool_calls[1].arguments

    class DummyCM:
        pass

    toolbox = AgentToolbox(contract_manager=DummyCM())  # type: ignore[arg-type]
    obs = toolbox.execute_tool(
        tool_resp.tool_calls[1].name,
        tool_resp.tool_calls[1].arguments,
    )
    assert obs["ok"] is False
    assert "Malformed JSON tool arguments" in obs["error"]


def test_data_uri_http_handshake_and_hash_verification() -> None:
    """A4: Verify ProviderAgent hosts deliverables over HTTP dataUri and EvaluatorAgent verifies keccak256 hash before LLM judge."""
    from web3 import Web3

    class StubChainManager:
        def __init__(self) -> None:
            self.jobs: dict[int, dict[str, Any]] = {}
            self.completed: list[int] = []
            self.rejected: list[tuple[int, str]] = []

        def submit_result(
            self,
            job_id: int,
            deliverable_text: str,
            provider_private_key: str | None = None,
            data_uri: str = "",
        ) -> dict[str, Any]:
            # Match ContractManager.get_job formatting: "0x" + bytes(raw[8]).hex() (always 64 hex chars)
            result_hash = "0x" + bytes(Web3.keccak(text=deliverable_text)).hex()
            self.jobs[job_id] = {
                "job_id": job_id,
                "result_hash": result_hash,
                "data_uri": data_uri,
                "state": "Submitted",
                "state_code": 2,
            }
            return {
                "tx_hash": f"0xsub_{job_id}",
                "job_id": job_id,
                "result_hash": result_hash,
                "data_uri": data_uri,
            }

        def get_job(self, job_id: int) -> dict[str, Any]:
            return self.jobs[job_id]

        def complete_job(self, job_id: int) -> dict[str, Any]:
            self.completed.append(job_id)
            self.jobs[job_id]["state"] = "Completed"
            return {"tx_hash": f"0xcomp_{job_id}", "job_id": job_id, "state": "Completed"}

        def reject_job(self, job_id: int, reason: str) -> dict[str, Any]:
            self.rejected.append((job_id, reason))
            self.jobs[job_id]["state"] = "Rejected"
            return {"tx_hash": f"0xrej_{job_id}", "job_id": job_id, "state": "Rejected", "reason": reason}

    llm_calls: list[list[dict[str, Any]]] = []

    class SpyJudgeLLM:
        def chat_json(
            self,
            messages: list[dict[str, Any]],
            required_keys: tuple[str, ...] = ("verdict", "score", "reasons"),
            model: str | None = None,
        ) -> dict[str, Any]:
            llm_calls.append(messages)
            return {"verdict": "PASS", "score": 96, "reasons": ["Verified 30 addresses via HTTP dataUri"]}

    cm = StubChainManager()
    provider_b = ProviderAgent(
        name="Provider B",
        mode="honest",
        private_key="0x" + "11" * 32,
        contract_manager=cm,  # type: ignore[arg-type]
    )
    evaluator = EvaluatorAgent(
        contract_manager=cm,  # type: ignore[arg-type]
        llm_client=SpyJudgeLLM(),  # type: ignore[arg-type]
    )

    try:
        # 1. Provider B produces deliverable, serves it via local HTTP server, and submits dataUri + resultHash on-chain
        sub_res = provider_b.submit_for_job(job_id=201, task_desc="30-address fund flow trace")
        data_uri = sub_res["data_uri"]
        assert data_uri.startswith("http://127.0.0.1:")
        assert "/deliverables/201" in data_uri

        # Verify fetch_deliverable downloads the exact deliverable over HTTP
        downloaded = fetch_deliverable(data_uri)
        assert downloaded == sub_res["deliverable"]

        # 2. EvaluatorAgent fetches deliverable from on-chain dataUri (without deliverable_content passed in memory!),
        # verifies keccak256 hash matches on-chain resultHash, and invokes LLM Judge -> completeJob
        eval_res = evaluator.evaluate_and_settle(
            job_id=201,
            task_requirement="30-address fund flow trace",
            acceptance_criteria=["30 address flows", "complete fields"],
        )
        assert eval_res["verdict"] == "PASS"
        assert eval_res["action"] == "completeJob"
        assert cm.completed == [201]
        assert len(llm_calls) == 1

        # 3. Deliverable whose keccak256 digest starts with a leading '0' hex nibble ("deliverable_sample_11" -> 0x02f984...):
        # Must NOT have its leading '0' stripped by .lstrip("0x") and must pass hash verification!
        leading_zero_text = "deliverable_sample_11"
        assert bytes(Web3.keccak(text=leading_zero_text)).hex().startswith("0")
        sub_203 = provider_b.submit_for_job(job_id=203, task_desc="leading zero hash verification")
        provider_b.tamper_hosted_deliverable(203, leading_zero_text)
        cm.submit_result(job_id=203, deliverable_text=leading_zero_text, data_uri=sub_203["data_uri"])
        eval_leading_zero = evaluator.evaluate_and_settle(
            job_id=203,
            task_requirement="leading zero hash verification",
            acceptance_criteria=["exact hash match"],
        )
        assert eval_leading_zero["verdict"] == "PASS"
        assert eval_leading_zero["action"] == "completeJob"
        assert 203 in cm.completed
        assert len(llm_calls) == 2

        # 4. Tamper with the hosted deliverable content at HTTP endpoint for job 202 after on-chain submission:
        # EvaluatorAgent must detect keccak256 mismatch and immediately call rejectJob WITHOUT calling LLM!
        sub_res_2 = provider_b.submit_for_job(job_id=202, task_desc="30-address fund flow trace")
        provider_b.tamper_hosted_deliverable(202, "TAMPERED_MALICIOUS_PAYLOAD")

        eval_tampered = evaluator.evaluate_and_settle(
            job_id=202,
            task_requirement="30-address fund flow trace",
            acceptance_criteria=["30 address flows", "complete fields"],
        )
        assert eval_tampered["verdict"] == "FAIL"
        assert eval_tampered["action"] == "rejectJob"
        assert "hash mismatch" in eval_tampered["reasons"][0].lower()
        assert cm.rejected[-1][0] == 202
        # LLM judge was NOT called for the tampered deliverable
        assert len(llm_calls) == 2

        # 5. Zero-hash commitment bypass attempt (resultHash = 0x00..00 on-chain):
        # EvaluatorAgent must NOT skip hash verification and must reject immediately without calling LLM!
        sub_204 = provider_b.submit_for_job(job_id=204, task_desc="30-address fund flow trace")
        cm.jobs[204] = {
            "job_id": 204,
            "result_hash": "0x" + ("00" * 32),
            "data_uri": sub_204["data_uri"],
            "state": "Submitted",
            "state_code": 2,
        }
        eval_zero_hash = evaluator.evaluate_and_settle(
            job_id=204,
            task_requirement="30-address fund flow trace",
            acceptance_criteria=["30 address flows"],
        )
        assert eval_zero_hash["verdict"] == "FAIL"
        assert eval_zero_hash["action"] == "rejectJob"
        assert "hash mismatch" in eval_zero_hash["reasons"][0].lower()
        assert cm.rejected[-1][0] == 204
        assert len(llm_calls) == 2
    finally:
        provider_b.close()


