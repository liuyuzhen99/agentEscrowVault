"""Evaluator Agent (LLM-as-a-Judge) for inspecting deliverables and settling escrow jobs."""

from __future__ import annotations

import json
from typing import Any

from agent_runtime.contracts import ContractManager
from agent_runtime.llm import LLMClient, LLMError

JUDGE_SYSTEM_PROMPT = (
    "You are an independent, neutral Evaluator Agent (LLM-as-a-Judge) for on-chain escrow "
    "arbitration on Base Sepolia. Evaluate the provider's deliverable strictly against the "
    "original task requirement and hard acceptance criteria. Respond ONLY with a valid JSON "
    'object of the form: {"verdict": "PASS" | "FAIL", "score": <int 0-100>, "reasons": ["..."]}. '
    "A job may only PASS if every hard criterion is satisfied and score >= 80."
)


class EvaluatorAgent:
    """Arbitrates Submitted escrow jobs using LLM-as-a-Judge and triggers completeJob/rejectJob."""

    def __init__(
        self,
        contract_manager: ContractManager,
        llm_client: LLMClient,
        pass_threshold: int = 80,
    ) -> None:
        self._cm = contract_manager
        self._llm = llm_client
        self._pass_threshold = pass_threshold

    def evaluate_deliverable(
        self,
        task_requirement: str,
        acceptance_criteria: list[str],
        deliverable_content: str,
    ) -> dict[str, Any]:
        """Run LLM-as-a-Judge evaluation and validate output structure."""
        user_prompt = json.dumps(
            {
                "task_requirement": task_requirement,
                "acceptance_criteria": acceptance_criteria,
                "deliverable_content": deliverable_content,
            },
            ensure_ascii=False,
            indent=2,
        )
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        result = self._llm.chat_json(
            messages=messages,
            required_keys=("verdict", "score", "reasons"),
        )
        verdict = str(result.get("verdict", "")).upper()
        if verdict not in ("PASS", "FAIL"):
            raise LLMError(f"Invalid evaluator verdict '{verdict}', expected PASS or FAIL")

        try:
            score = int(result["score"])
        except (TypeError, ValueError) as exc:
            raise LLMError(f"Invalid evaluator score: {result.get('score')}") from exc

        if not (0 <= score <= 100):
            raise LLMError(f"Evaluator score {score} out of range 0..100")

        reasons = result.get("reasons")
        if not isinstance(reasons, list) or not reasons:
            raise LLMError("Evaluator reasons must be a non-empty list of strings")

        return {
            "verdict": verdict,
            "score": score,
            "reasons": [str(r) for r in reasons],
        }

    def evaluate_and_settle(
        self,
        job_id: int,
        task_requirement: str,
        acceptance_criteria: list[str],
        deliverable_content: str,
    ) -> dict[str, Any]:
        """Evaluate deliverable via LLM and execute completeJob or rejectJob on-chain."""
        judgment = self.evaluate_deliverable(
            task_requirement=task_requirement,
            acceptance_criteria=acceptance_criteria,
            deliverable_content=deliverable_content,
        )
        verdict = judgment["verdict"]
        score = judgment["score"]
        reasons = judgment["reasons"]

        if verdict == "PASS" and score >= self._pass_threshold:
            tx_res = self._cm.complete_job(job_id)
            return {
                **judgment,
                "action": "completeJob",
                "tx_hash": tx_res["tx_hash"],
                "state": "Completed",
            }

        reject_reason = reasons[0] if reasons else "Quality check failed"
        tx_res = self._cm.reject_job(job_id, reject_reason)
        return {
            **judgment,
            "action": "rejectJob",
            "tx_hash": tx_res["tx_hash"],
            "state": "Rejected",
            "rejection_reason": reject_reason,
        }
