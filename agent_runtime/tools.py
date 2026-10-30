"""Tool schemas and execution toolbox for the Client Agent ReAct loop."""

from __future__ import annotations

from typing import Any, Callable

from agent_runtime.contracts import USDC_SCALE, ContractManager
from agent_runtime.x402 import probe_quote

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "probe_quote",
            "description": (
                "Send an unauthenticated GET request to a resource URL to capture HTTP 402 "
                "Payment Required and parse its Base64 payment header (price_usd, pay_to, asset, type)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_url": {
                        "type": "string",
                        "description": "Target HTTP resource URL to probe for x402 pricing.",
                    }
                },
                "required": ["resource_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vault_status",
            "description": (
                "Query on-chain AgentVault remaining daily budget, maxPerTxDirect cap, "
                "maxPerTxEscrow cap, and whitelisted direct payees."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pay_direct",
            "description": (
                "Execute an immediate direct USDC transfer via AgentVault.spendDirect(to, amount) "
                "for small standardized API calls within maxPerTxDirect and payee whitelist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payee_address": {
                        "type": "string",
                        "description": "Recipient wallet address (must be whitelisted for direct spend).",
                    },
                    "amount_usd": {
                        "type": "number",
                        "description": "Amount in USDC (e.g. 0.005).",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason or resource URL for this direct payment.",
                    },
                },
                "required": ["payee_address", "amount_usd", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hire_escrow_job",
            "description": (
                "Lock USDC into AgentEscrow via AgentVault.fundJob to hire an external Provider Agent "
                "with on-chain Evaluator quality arbitration."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "provider_address": {
                        "type": "string",
                        "description": "Provider Agent address to fulfill the job.",
                    },
                    "evaluator_address": {
                        "type": "string",
                        "description": "Evaluator Agent address to inspect and settle the job.",
                    },
                    "amount_usd": {
                        "type": "number",
                        "description": "Escrow amount in USDC (must be <= maxPerTxEscrow).",
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Job deadline duration in seconds from current block timestamp.",
                    },
                    "task_desc": {
                        "type": "string",
                        "description": "Detailed task specification for the Provider and Evaluator.",
                    },
                },
                "required": [
                    "provider_address",
                    "evaluator_address",
                    "amount_usd",
                    "duration_seconds",
                    "task_desc",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_job",
            "description": (
                "Query on-chain AgentEscrow.jobs(jobId) for current job state "
                "(Funded, Submitted, Completed, Rejected, Expired), resultHash, and deliverable."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "On-chain escrow job ID.",
                    }
                },
                "required": ["job_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_task",
            "description": (
                "Submit the synthesized final deliverable report and conclude the agent task."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "final_report": {
                        "type": "string",
                        "description": "Final synthesized report fulfilling the user's goal.",
                    }
                },
                "required": ["final_report"],
            },
        },
    },
]


class AgentToolbox:
    """Executes tool calls requested by the LLM and formats observations."""

    def __init__(
        self,
        contract_manager: ContractManager,
        on_direct_paid_hook: Callable[[str, float, str], str | None] | None = None,
        on_job_hired_hook: Callable[[int, str, str, float, str], dict[str, Any] | None] | None = None,
        job_metadata_store: dict[int, dict[str, Any]] | None = None,
        http_get: Callable[[str, int], tuple[int, dict[str, str], str]] | None = None,
    ) -> None:
        self._cm = contract_manager
        self._on_direct_paid_hook = on_direct_paid_hook
        self._on_job_hired_hook = on_job_hired_hook
        self._job_metadata: dict[int, dict[str, Any]] = (
            job_metadata_store if job_metadata_store is not None else {}
        )
        self._http_get = http_get

    @property
    def job_metadata(self) -> dict[int, dict[str, Any]]:
        return self._job_metadata

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a tool invocation and return a JSON-serializable observation dict."""
        try:
            if name == "probe_quote":
                quote = probe_quote(
                    str(arguments["resource_url"]), http_get=self._http_get
                )
                return {"ok": quote.get("status_code") == 402, **quote}

            if name == "get_vault_status":
                status = self._cm.get_vault_status()
                return {"ok": True, **status}

            if name == "pay_direct":
                payee = str(arguments["payee_address"])
                amount_usd = float(arguments["amount_usd"])
                reason = str(arguments.get("reason", ""))
                amount_raw = int(round(amount_usd * USDC_SCALE))
                tx_info = self._cm.spend_direct(payee, amount_raw)
                data_payload = None
                if self._on_direct_paid_hook is not None:
                    data_payload = self._on_direct_paid_hook(
                        payee, amount_usd, tx_info["tx_hash"]
                    )
                result: dict[str, Any] = {"ok": True, **tx_info}
                if data_payload is not None:
                    result["data"] = data_payload
                return result

            if name == "hire_escrow_job":
                provider = str(arguments["provider_address"])
                evaluator = str(arguments["evaluator_address"])
                amount_usd = float(arguments["amount_usd"])
                duration = int(arguments["duration_seconds"])
                task_desc = str(arguments.get("task_desc", ""))
                amount_raw = int(round(amount_usd * USDC_SCALE))
                tx_info = self._cm.fund_job(provider, evaluator, amount_raw, duration)
                job_id = int(tx_info["job_id"])
                self._job_metadata[job_id] = {"task_desc": task_desc}
                if self._on_job_hired_hook is not None:
                    hook_meta = self._on_job_hired_hook(
                        job_id, provider, evaluator, amount_usd, task_desc
                    )
                    if hook_meta:
                        self._job_metadata[job_id].update(hook_meta)
                return {"ok": True, **tx_info}

            if name == "inspect_job":
                job_id = int(arguments["job_id"])
                job_info = self._cm.get_job(job_id)
                extra = self._job_metadata.get(job_id, {})
                return {"ok": True, **job_info, **extra}

            if name == "finish_task":
                report = str(arguments["final_report"])
                return {"ok": True, "finished": True, "final_report": report}

            return {"ok": False, "error": f"Unknown tool '{name}'"}
        except Exception as exc:
            # Deliberate domain feedback for ReAct self-healing: surface on-chain reverts
            # or HTTP errors as structured tool observations so the LLM can re-plan.
            return {"ok": False, "tool": name, "error": str(exc)}
