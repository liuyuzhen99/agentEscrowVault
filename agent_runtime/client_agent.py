"""Client Agent running a pure LLM ReAct (Reasoning + Acting) loop with financial constraints."""

from __future__ import annotations

import json
from typing import Any

from agent_runtime.llm import LLMClient
from agent_runtime.tools import TOOL_SCHEMAS, AgentToolbox

CLIENT_SYSTEM_PROMPT = (
    "You are an autonomous Web3 Client Agent operating an on-chain AgentVault and AgentEscrow "
    "on Base Sepolia. You hold a restricted session key.\n"
    "Follow the ReAct loop strictly using the provided tools:\n"
    "1. Inspect the vault status (`get_vault_status`) and probe candidate service URLs (`probe_quote`).\n"
    "2. Choose the settlement route based on the vault's on-chain limits and the service quote:\n"
    "   - Direct spend (`pay_direct`) only works for whitelisted payees up to `max_per_tx_direct_usd`.\n"
    "   - For larger or custom analysis tasks up to `max_per_tx_escrow_usd`, lock funds in `AgentEscrow` "
    "via `hire_escrow_job`.\n"
    "3. If a direct payment attempt reverts or exceeds the cap, reflect on the error observation "
    "and switch to `hire_escrow_job`.\n"
    "4. After hiring an escrow job, call `inspect_job` to check the Evaluator's arbitration verdict:\n"
    "   - If the job state is `Rejected` (fraudulent/low-quality deliverable rejected and funds "
    "refunded to the vault), reflect on the failure, avoid the bad provider, and hire an "
    "alternative higher-quality provider from the market.\n"
    "   - Once the job state is `Completed` (or direct data is acquired), call `finish_task` with "
    "the final report."
)


class ClientAgent:
    """Autonomous buyer agent driven 100% by LLM tool_calls and tool observations."""

    def __init__(
        self,
        llm_client: LLMClient,
        toolbox: AgentToolbox,
        evaluator_address: str = "",
        max_steps: int = 15,
    ) -> None:
        self._llm = llm_client
        self._toolbox = toolbox
        self._evaluator_address = evaluator_address
        self._max_steps = max_steps

    def run(
        self,
        user_goal: str,
        market_resources: list[str],
    ) -> dict[str, Any]:
        """Run the LLM ReAct loop until `finish_task` is invoked or `max_steps` is reached."""
        initial_context = {
            "user_goal": user_goal,
            "market_resources": market_resources,
            "default_evaluator_address": self._evaluator_address,
        }
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": CLIENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(initial_context, ensure_ascii=False, indent=2),
            },
        ]
        trace: list[dict[str, Any]] = []

        for step_idx in range(1, self._max_steps + 1):
            llm_resp = self._llm.chat_with_tools(
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": llm_resp.content,
            }
            if llm_resp.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in llm_resp.tool_calls
                ]
            messages.append(assistant_msg)

            if not llm_resp.tool_calls:
                trace.append(
                    {
                        "step": step_idx,
                        "thought": llm_resp.content,
                        "tool_calls": [],
                    }
                )
                continue

            for tc in llm_resp.tool_calls:
                observation = self._toolbox.execute_tool(tc.name, tc.arguments)
                trace.append(
                    {
                        "step": step_idx,
                        "thought": llm_resp.content,
                        "tool": tc.name,
                        "arguments": tc.arguments,
                        "observation": observation,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": json.dumps(observation, ensure_ascii=False),
                    }
                )
                if tc.name == "finish_task" and observation.get("finished") is True:
                    return {
                        "finished": True,
                        "steps": step_idx,
                        "final_report": observation["final_report"],
                        "trace": trace,
                        "messages": messages,
                    }

        raise RuntimeError(
            f"ClientAgent exceeded max_steps ({self._max_steps}) without calling finish_task"
        )
