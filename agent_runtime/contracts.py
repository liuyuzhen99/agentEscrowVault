"""Web3 contract manager for AgentVault, AgentEscrow, and USDC on Base Sepolia / EVM."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eth_account import Account
from web3 import Web3
from web3._utils.events import EventLogErrorFlags
from web3.contract import Contract

USDC_DECIMALS = 6
USDC_SCALE = 10**USDC_DECIMALS

JOB_STATE_NAMES = {
    0: "None",
    1: "Funded",
    2: "Submitted",
    3: "Completed",
    4: "Rejected",
    5: "Expired",
}


def _load_foundry_artifact(contract_name: str) -> dict[str, Any]:
    """Load ABI and bytecode from Foundry compilation output relative to module path."""
    repo_root = Path(__file__).resolve().parent.parent
    artifact_path = (
        repo_root
        / "contracts"
        / "out"
        / f"{contract_name}.sol"
        / f"{contract_name}.json"
    )
    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Foundry artifact not found at {artifact_path}. Run `forge build` first."
        )
    return json.loads(artifact_path.read_text(encoding="utf-8"))


class ContractManager:
    """Single entry point for all Web3 RPC calls and transaction signing."""

    def __init__(
        self,
        w3: Web3,
        usdc_address: str,
        vault_address: str,
        escrow_address: str,
        agent_session_private_key: str | None = None,
        owner_private_key: str | None = None,
        evaluator_private_key: str | None = None,
        known_payees: list[str] | None = None,
    ) -> None:
        self._w3 = w3
        self._usdc_address = Web3.to_checksum_address(usdc_address)
        self._vault_address = Web3.to_checksum_address(vault_address)
        self._escrow_address = Web3.to_checksum_address(escrow_address)
        self._agent_key = agent_session_private_key or ""
        self._owner_key = owner_private_key or ""
        self._evaluator_key = evaluator_private_key or ""
        self._known_payees = [
            Web3.to_checksum_address(addr) for addr in (known_payees or [])
        ]

        vault_artifact = _load_foundry_artifact("AgentVault")
        escrow_artifact = _load_foundry_artifact("AgentEscrow")
        erc20_artifact = _load_foundry_artifact("IERC20")

        self._vault: Contract = self._w3.eth.contract(
            address=self._vault_address, abi=vault_artifact["abi"]
        )
        self._escrow: Contract = self._w3.eth.contract(
            address=self._escrow_address, abi=escrow_artifact["abi"]
        )
        self._usdc: Contract = self._w3.eth.contract(
            address=self._usdc_address, abi=erc20_artifact["abi"]
        )

    @property
    def w3(self) -> Web3:
        return self._w3

    @property
    def vault_address(self) -> str:
        return self._vault_address

    @property
    def escrow_address(self) -> str:
        return self._escrow_address

    @property
    def usdc_address(self) -> str:
        return self._usdc_address

    def _send_tx(self, func_call: Any, private_key: str) -> Any:
        if not private_key:
            raise ValueError("Private key required to sign and broadcast transaction")
        acct = Account.from_key(private_key)
        nonce = self._w3.eth.get_transaction_count(acct.address, "pending")
        tx = func_call.build_transaction(
            {
                "from": acct.address,
                "nonce": nonce,
                "chainId": self._w3.eth.chain_id,
                "gas": 500_000,
                "gasPrice": self._w3.eth.gas_price,
            }
        )
        # Estimate / simulate first via call so Solidity revert errors surface clearly
        func_call.call({"from": acct.address})
        signed = self._w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt["status"] != 1:
            raise RuntimeError(f"Transaction {tx_hash.hex()} reverted on-chain")
        return receipt

    def get_vault_status(self, candidate_payees: list[str] | None = None) -> dict[str, Any]:
        """Query on-chain AgentVault limits, remaining daily budget, and whitelisted payees."""
        balance_raw = self._usdc.functions.balanceOf(self._vault_address).call()
        max_direct_raw = self._vault.functions.maxPerTxDirect().call()
        max_escrow_raw = self._vault.functions.maxPerTxEscrow().call()
        max_daily_raw = self._vault.functions.maxDailySpend().call()
        daily_spent_raw = self._vault.functions.dailySpendCounter().call()
        window_start = self._vault.functions.windowStartTimestamp().call()
        paused = self._vault.functions.paused().call()

        latest_ts = self._w3.eth.get_block("latest")["timestamp"]
        if latest_ts >= window_start + 86400:
            effective_daily_spent_raw = 0
        else:
            effective_daily_spent_raw = daily_spent_raw

        remaining_daily_raw = max(0, max_daily_raw - effective_daily_spent_raw)
        payees_to_check = list(self._known_payees)
        if candidate_payees:
            for p in candidate_payees:
                cs = Web3.to_checksum_address(p)
                if cs not in payees_to_check:
                    payees_to_check.append(cs)

        whitelisted: list[str] = []
        for addr in payees_to_check:
            if self._vault.functions.isWhitelistedPayee(addr).call():
                whitelisted.append(addr)

        return {
            "vault_address": self._vault_address,
            "escrow_address": self._escrow_address,
            "vault_balance_usd": round(balance_raw / USDC_SCALE, 6),
            "max_per_tx_direct_usd": round(max_direct_raw / USDC_SCALE, 6),
            "max_per_tx_escrow_usd": round(max_escrow_raw / USDC_SCALE, 6),
            "max_daily_spend_usd": round(max_daily_raw / USDC_SCALE, 6),
            "daily_spend_counter_usd": round(effective_daily_spent_raw / USDC_SCALE, 6),
            "remaining_daily_budget_usd": round(remaining_daily_raw / USDC_SCALE, 6),
            "paused": bool(paused),
            "whitelisted_payees": whitelisted,
        }

    def spend_direct(self, payee_address: str, amount_raw: int) -> dict[str, Any]:
        """Execute AgentVault.spendDirect using the Agent Session Key."""
        payee_cs = Web3.to_checksum_address(payee_address)
        call = self._vault.functions.spendDirect(payee_cs, int(amount_raw))
        receipt = self._send_tx(call, self._agent_key)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "payee": payee_cs,
            "amount_raw": int(amount_raw),
            "amount_usd": round(amount_raw / USDC_SCALE, 6),
        }

    def fund_job(
        self,
        provider_address: str,
        evaluator_address: str,
        amount_raw: int,
        duration_seconds: int,
    ) -> dict[str, Any]:
        """Execute AgentVault.fundJob to lock USDC into AgentEscrow."""
        provider_cs = Web3.to_checksum_address(provider_address)
        evaluator_cs = Web3.to_checksum_address(evaluator_address)
        latest_ts = self._w3.eth.get_block("latest")["timestamp"]
        deadline = int(latest_ts + int(duration_seconds))
        call = self._vault.functions.fundJob(
            self._escrow_address,
            provider_cs,
            evaluator_cs,
            int(amount_raw),
            deadline,
        )
        receipt = self._send_tx(call, self._agent_key)
        logs = self._escrow.events.JobCreated().process_receipt(
            receipt, errors=EventLogErrorFlags.Discard
        )
        matched_logs = [log for log in logs if "args" in log and "jobId" in log["args"]]
        job_id = (
            int(matched_logs[0]["args"]["jobId"])
            if matched_logs
            else int(self._escrow.functions.nextJobId().call())
        )
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "job_id": job_id,
            "provider": provider_cs,
            "evaluator": evaluator_cs,
            "amount_raw": int(amount_raw),
            "amount_usd": round(amount_raw / USDC_SCALE, 6),
            "deadline": deadline,
        }

    def submit_result(
        self, job_id: int, result_hash: bytes, provider_private_key: str
    ) -> dict[str, Any]:
        """Execute AgentEscrow.submitResult on behalf of the Provider Agent."""
        call = self._escrow.functions.submitResult(int(job_id), result_hash)
        receipt = self._send_tx(call, provider_private_key)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "job_id": int(job_id),
            "result_hash": "0x" + result_hash.hex(),
        }

    def complete_job(self, job_id: int) -> dict[str, Any]:
        """Execute AgentEscrow.completeJob as the Evaluator Agent."""
        call = self._escrow.functions.completeJob(int(job_id))
        receipt = self._send_tx(call, self._evaluator_key)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "job_id": int(job_id),
            "state": "Completed",
        }

    def reject_job(self, job_id: int, reason: str) -> dict[str, Any]:
        """Execute AgentEscrow.rejectJob as the Evaluator Agent."""
        call = self._escrow.functions.rejectJob(int(job_id), str(reason))
        receipt = self._send_tx(call, self._evaluator_key)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "job_id": int(job_id),
            "state": "Rejected",
            "reason": str(reason),
        }

    def claim_timeout_refund(self, job_id: int, caller_private_key: str | None = None) -> dict[str, Any]:
        """Execute AgentEscrow.claimTimeoutRefund after deadline expiration."""
        key = caller_private_key or self._agent_key or self._owner_key
        call = self._escrow.functions.claimTimeoutRefund(int(job_id))
        receipt = self._send_tx(call, key)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "job_id": int(job_id),
            "state": "Expired",
        }

    def get_job(self, job_id: int) -> dict[str, Any]:
        """Inspect on-chain job struct from AgentEscrow.jobs(jobId)."""
        raw = self._escrow.functions.jobs(int(job_id)).call()
        state_code = int(raw[7])
        return {
            "job_id": int(raw[0]),
            "client": str(raw[1]),
            "provider": str(raw[2]),
            "evaluator": str(raw[3]),
            "amount_raw": int(raw[4]),
            "amount_usd": round(int(raw[4]) / USDC_SCALE, 6),
            "deadline": int(raw[5]),
            "result_hash": "0x" + bytes(raw[6]).hex(),
            "state_code": state_code,
            "state": JOB_STATE_NAMES.get(state_code, "Unknown"),
        }
