"""Provider Agent that verifies escrow funding and submits deliverable hashes on-chain."""

from __future__ import annotations

from typing import Any, Callable

from web3 import Web3

from agent_runtime.contracts import ContractManager


class ProviderAgent:
    """Independent Provider Agent that only works after verifying JobState.Funded on-chain."""

    def __init__(
        self,
        name: str,
        address: str,
        private_key: str,
        contract_manager: ContractManager,
        deliverable_generator: Callable[[int, str], str],
    ) -> None:
        self._name = name
        self._address = Web3.to_checksum_address(address)
        self._private_key = private_key
        self._cm = contract_manager
        self._generator = deliverable_generator

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    def fulfill_job(self, job_id: int, task_desc: str) -> dict[str, Any]:
        """Verify job is Funded for this provider, produce deliverable, and call submitResult."""
        job = self._cm.get_job(job_id)
        if job["state"] != "Funded":
            raise RuntimeError(
                f"Provider {self._name} refuses job {job_id}: expected state Funded, got {job['state']}"
            )
        if Web3.to_checksum_address(job["provider"]) != self._address:
            raise RuntimeError(
                f"Provider {self._name} ({self._address}) is not assigned to job {job_id} ({job['provider']})"
            )

        deliverable_text = self._generator(job_id, task_desc)
        result_hash: bytes = Web3.keccak(text=deliverable_text)
        tx_res = self._cm.submit_result(
            job_id=job_id,
            result_hash=result_hash,
            provider_private_key=self._private_key,
        )
        return {
            "job_id": job_id,
            "provider": self._address,
            "deliverable": deliverable_text,
            "result_hash": tx_res["result_hash"],
            "tx_hash": tx_res["tx_hash"],
        }
