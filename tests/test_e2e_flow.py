"""End-to-end integration tests for AgentEscrowVault (E2E-01, E2E-02, E2E-03, E2E-04).

Runs real compiled Solidity contracts (AgentVault.sol + AgentEscrow.sol) on a live Anvil
EVM node, serves x402 Payment Required quotes and HTTP deliverables (dataUri), and drives
the ClientAgent + EvaluatorAgent via real OpenAI-compatible LLM API (from .env when
LLM_API_KEY is present, with deterministic offline fallback when FORCE_OFFLINE_LLM=1).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any, Callable

import pytest
from eth_account import Account
from web3 import Web3

from agent_runtime.client_agent import ClientAgent
from agent_runtime.config import LLMConfig, load_config
from agent_runtime.contracts import USDC_SCALE, ContractManager, _load_foundry_artifact
from agent_runtime.evaluator import EvaluatorAgent
from agent_runtime.llm import LLMClient
from agent_runtime.provider import ProviderAgent
from agent_runtime.tools import AgentToolbox
from agent_runtime.x402 import encode_x402_header, fetch_deliverable

# Deterministic Anvil test accounts (standard mnemonic)
OWNER_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
SESSION_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
MERCHANT_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
PROVIDER_A_KEY = "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
PROVIDER_B_KEY = "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
EVALUATOR_KEY = "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"


def _build_realistic_30_address_report(
    task_desc: str = "Deep Token Laundering Penetration Analysis",
) -> str:
    """Generate a realistic, cryptographically distinct 30-address laundering penetration report."""
    from datetime import datetime, timedelta, timezone

    now_utc = datetime.now(timezone.utc)
    ref_ts = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    typologies = [
        "peel_chain_layering",
        "tornado_style_mixer_hop",
        "smurfing_fan_out",
        "cross_bridge_rapid_swap",
        "nested_cex_deposit_consolidation",
    ]
    rows: list[str] = []
    for i in range(1, 31):
        tx_h = "0x" + Web3.keccak(text=f"base_sepolia_tx_{i}").hex().removeprefix("0x")
        src_addr = Web3.to_checksum_address(
            "0x" + Web3.keccak(text=f"laundering_src_{i}").hex().removeprefix("0x")[:40]
        )
        dst_addr = Web3.to_checksum_address(
            "0x" + Web3.keccak(text=f"laundering_dst_{i}").hex().removeprefix("0x")[:40]
        )
        hours_ago = i * 4
        days_ago = round(hours_ago / 24.0, 2)
        ts_iso = (now_utc - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        amt = round(1250.50 + (i * 317.25), 2)
        risk = 78 + (i % 21)
        typo = typologies[i % len(typologies)]
        rows.append(
            f"Flow #{i:02d} | timestamp={ts_iso} ({hours_ago}h / {days_ago}d ago, within 7 days of {ref_ts}) | "
            f"tx_hash={tx_h} | from_address={src_addr} | to_address={dst_addr} | amount_usdc={amt} USDC | "
            f"token=USDC (0x036CbD53842c5426634e7929541eC2318f3dCF7e) | chain_id=84532 (Base Sepolia) | "
            f"hop_depth={(i % 5) + 1} | typology={typo} | risk_score={risk}/100 | "
            f"penetration_finding=Traced {amt} USDC hop #{(i % 5) + 1} via {typo} to cluster #{(i % 4) + 1}"
        )
    return (
        "Executive Summary: Deep Fund Penetration & Laundering Typology Report (Base Sepolia, 7-Day Window)\n"
        f"Task Requirement Addressed: {task_desc}\n"
        f"Reference Evaluation Timestamp (UTC): {ref_ts} (All 30 flows occurred 4h to 120h / 0.17d to 5.0d prior to {ref_ts}, strictly within 7 days)\n"
        "Total Verified Flows: 30 distinct on-chain address flows (Flows #01 through #30) with complete fields.\n"
        "Key Findings: Identified 4 laundering clusters using peel-chain layering, smurfing fan-out, and cross-bridge swaps.\n\n"
        + "\n".join(rows)
    )


def _build_e2e_llm_client(
    fallback_transport: Callable[[str, dict[str, str], dict[str, Any], int], tuple[int, str]],
) -> LLMClient:
    """Use real configured LLM API from .env by default; fall back to offline transport if forced or unconfigured."""
    force_offline = os.environ.get("FORCE_OFFLINE_LLM", "").strip() == "1"
    runtime_cfg = load_config()
    if not force_offline and runtime_cfg.llm.api_key:
        return LLMClient(runtime_cfg.llm)

    offline_cfg = LLMConfig(
        api_key="sk-e2e-offline",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        client_model="gpt-4o-mini",
        evaluator_model="gpt-4o-mini",
        temperature=0.0,
        timeout_seconds=10,
    )
    return LLMClient(offline_cfg, transport=fallback_transport)


def _deploy_contract(w3: Web3, deployer_key: str, contract_name: str, *ctor_args: Any) -> str:
    artifact = _load_foundry_artifact(contract_name)
    abi = artifact["abi"]
    bytecode = artifact["bytecode"]["object"]
    acct = Account.from_key(deployer_key)
    contract_cls = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = contract_cls.constructor(*ctor_args).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "chainId": w3.eth.chain_id,
            "gas": 3_000_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = w3.eth.account.sign_transaction(tx, private_key=deployer_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt["status"] == 1
    return str(receipt["contractAddress"])


@pytest.fixture()
def anvil_env() -> Any:
    """Start a fresh local Anvil EVM node (chainId 84532 Base Sepolia) and deploy contracts."""
    port = 18545
    proc = subprocess.Popen(
        ["anvil", "--port", str(port), "--chain-id", "84532", "--silent"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rpc_url = f"http://127.0.0.1:{port}"
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    for _ in range(30):
        try:
            if w3.is_connected():
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError("Failed to start local Anvil node")

    try:
        owner_acct = Account.from_key(OWNER_KEY)
        session_acct = Account.from_key(SESSION_KEY)
        merchant_acct = Account.from_key(MERCHANT_KEY)
        provider_a_acct = Account.from_key(PROVIDER_A_KEY)
        provider_b_acct = Account.from_key(PROVIDER_B_KEY)
        evaluator_acct = Account.from_key(EVALUATOR_KEY)

        usdc_addr = _deploy_contract(w3, OWNER_KEY, "MockUSDC")
        vault_addr = _deploy_contract(w3, OWNER_KEY, "AgentVault", usdc_addr, session_acct.address)
        escrow_addr = _deploy_contract(w3, OWNER_KEY, "AgentEscrow", usdc_addr)

        # Configure Vault whitelist & approved escrow, and mint 0.10 USDC initial budget to Vault
        usdc_art = _load_foundry_artifact("MockUSDC")
        vault_art = _load_foundry_artifact("AgentVault")
        usdc_contract = w3.eth.contract(address=usdc_addr, abi=usdc_art["abi"])
        vault_contract = w3.eth.contract(address=vault_addr, abi=vault_art["abi"])

        for fn_call in (
            vault_contract.functions.setPayeeWhitelist(merchant_acct.address, True),
            vault_contract.functions.setEscrowApproved(escrow_addr, True),
            usdc_contract.functions.mint(vault_addr, int(0.10 * USDC_SCALE)),
        ):
            tx = fn_call.build_transaction(
                {
                    "from": owner_acct.address,
                    "nonce": w3.eth.get_transaction_count(owner_acct.address),
                    "chainId": w3.eth.chain_id,
                    "gas": 300_000,
                    "gasPrice": w3.eth.gas_price,
                }
            )
            signed = w3.eth.account.sign_transaction(tx, private_key=OWNER_KEY)
            tx_h = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_h)

        cm = ContractManager(
            w3=w3,
            usdc_address=usdc_addr,
            vault_address=vault_addr,
            escrow_address=escrow_addr,
            agent_session_private_key=SESSION_KEY,
            owner_private_key=OWNER_KEY,
            evaluator_private_key=EVALUATOR_KEY,
            known_payees=[
                merchant_acct.address,
                provider_a_acct.address,
                provider_b_acct.address,
            ],
        )

        yield {
            "w3": w3,
            "cm": cm,
            "usdc_contract": usdc_contract,
            "owner": owner_acct.address,
            "session": session_acct.address,
            "merchant": merchant_acct.address,
            "provider_a": provider_a_acct.address,
            "provider_b": provider_b_acct.address,
            "evaluator": evaluator_acct.address,
        }
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


# ============================================================================
# E2E-01: Small-value Immediate Direct Spend (0.005 USDC <= 0.01 USDC cap)
# ============================================================================


def test_e2e_01_direct_spend(anvil_env: dict[str, Any]) -> None:
    """E2E-01: Agent probes 0.005 USDC x402 API, verifies whitelist, pays directly, gets data."""
    cm: ContractManager = anvil_env["cm"]
    usdc_contract = anvil_env["usdc_contract"]
    merchant_addr: str = anvil_env["merchant"]

    quote_header = encode_x402_header(
        {
            "price_usd": 0.005,
            "pay_to": merchant_addr,
            "asset": cm.usdc_address,
            "type": "direct",
            "description": "Real-time Base Sepolia gas feed",
        }
    )

    def http_get_402(url: str, timeout: int) -> tuple[int, dict[str, str], str]:
        return 402, {"X-Payment-Required": quote_header}, '{"error": "Payment Required"}'

    def on_direct_paid(payee: str, amount_usd: float, tx_hash: str) -> str:
        return json.dumps(
            {
                "base_fee_gwei": 0.0012,
                "priority_fee_gwei": 0.0005,
                "settled_tx": tx_hash,
            }
        )

    def e2e_01_llm_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        msgs = body["messages"]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]
        if not tool_msgs:
            resp = {
                "id": "e2e01-1",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Inspecting vault status and probing x402 quote.",
                            "tool_calls": [
                                {
                                    "id": "call_vstatus",
                                    "type": "function",
                                    "function": {"name": "get_vault_status", "arguments": "{}"},
                                },
                                {
                                    "id": "call_probe",
                                    "type": "function",
                                    "function": {
                                        "name": "probe_quote",
                                        "arguments": json.dumps(
                                            {"resource_url": "http://merchant.local/api/gas"}
                                        ),
                                    },
                                },
                            ],
                        }
                    }
                ],
            }
            return 200, json.dumps(resp)

        paid_msgs = [m for m in tool_msgs if m.get("name") == "pay_direct"]
        if not paid_msgs:
            probe_obs = next(
                json.loads(m["content"]) for m in tool_msgs if m.get("name") == "probe_quote"
            )
            resp = {
                "id": "e2e01-2",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Quote is 0.005 USDC <= 0.01 direct cap and payee is whitelisted. Calling pay_direct.",
                            "tool_calls": [
                                {
                                    "id": "call_pay_direct",
                                    "type": "function",
                                    "function": {
                                        "name": "pay_direct",
                                        "arguments": json.dumps(
                                            {
                                                "payee_address": probe_obs["pay_to"],
                                                "amount_usd": probe_obs["price_usd"],
                                                "reason": "Purchase Base gas feed",
                                            }
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            }
            return 200, json.dumps(resp)

        pay_obs = json.loads(paid_msgs[-1]["content"])
        resp = {
            "id": "e2e01-3",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Direct payment settled on-chain and data received. Finishing task.",
                        "tool_calls": [
                            {
                                "id": "call_finish",
                                "type": "function",
                                "function": {
                                    "name": "finish_task",
                                    "arguments": json.dumps(
                                        {
                                            "final_report": f"Gas feed acquired via tx {pay_obs['tx_hash']}: {pay_obs['data']}"
                                        }
                                    ),
                                },
                            }
                        ],
                    }
                }
            ],
        }
        return 200, json.dumps(resp)

    llm_client = _build_e2e_llm_client(e2e_01_llm_transport)
    toolbox = AgentToolbox(
        contract_manager=cm,
        on_direct_paid_hook=on_direct_paid,
        http_get=http_get_402,
    )
    agent = ClientAgent(llm_client=llm_client, toolbox=toolbox, evaluator_address=anvil_env["evaluator"])

    res = agent.run(
        user_goal=(
            "Fetch real-time Base gas price breakdown from http://merchant.local/api/gas. "
            "Probe the quote, pay directly via pay_direct, and include the exact base_fee_gwei in finish_task."
        ),
        market_resources=["http://merchant.local/api/gas"],
    )

    assert res["finished"] is True
    assert "0.0012" in res["final_report"] or "base_fee_gwei" in res["final_report"]
    assert usdc_contract.functions.balanceOf(merchant_addr).call() == 5_000
    assert usdc_contract.functions.balanceOf(cm.vault_address).call() == 95_000


# ============================================================================
# E2E-02: Direct Cap Intercept & Self-Healing Switch to Escrow (0.05 USDC)
# ============================================================================


def test_e2e_02_cap_intercept_switch_escrow(anvil_env: dict[str, Any]) -> None:
    """E2E-02: Agent attempts 0.05 USDC direct pay -> reverted on-chain -> switches to Escrow."""
    cm: ContractManager = anvil_env["cm"]
    usdc_contract = anvil_env["usdc_contract"]
    provider_b_addr: str = anvil_env["provider_b"]
    evaluator_addr: str = anvil_env["evaluator"]

    # Whitelist provider B as a direct payee so only the 0.01 USDC cap intercepts the 0.05 direct attempt
    vault_art = _load_foundry_artifact("AgentVault")
    vault_contract = cm.w3.eth.contract(address=cm.vault_address, abi=vault_art["abi"])
    tx = vault_contract.functions.setPayeeWhitelist(provider_b_addr, True).build_transaction(
        {
            "from": anvil_env["owner"],
            "nonce": cm.w3.eth.get_transaction_count(anvil_env["owner"]),
            "chainId": cm.w3.eth.chain_id,
            "gas": 200_000,
            "gasPrice": cm.w3.eth.gas_price,
        }
    )
    signed = cm.w3.eth.account.sign_transaction(tx, private_key=OWNER_KEY)
    tx_h = cm.w3.eth.send_raw_transaction(signed.raw_transaction)
    cm.w3.eth.wait_for_transaction_receipt(tx_h)

    quote_header = encode_x402_header(
        {
            "price_usd": 0.05,
            "pay_to": provider_b_addr,
            "asset": cm.usdc_address,
            "type": "escrow",
            "description": "Deep Token Laundering Penetration Analysis",
        }
    )

    def http_get_402(url: str, timeout: int) -> tuple[int, dict[str, str], str]:
        return 402, {"X-Payment-Required": quote_header}, '{"error": "Payment Required"}'

    provider_b = ProviderAgent(
        name="ProviderB",
        address=provider_b_addr,
        private_key=PROVIDER_B_KEY,
        contract_manager=cm,
        deliverable_generator=lambda job_id, desc: _build_realistic_30_address_report(desc),
    )

    def judge_llm_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        return 200, json.dumps(
            {
                "id": "judge-1",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "verdict": "PASS",
                                    "score": 95,
                                    "reasons": ["30 address flows verified and complete"],
                                }
                            ),
                        }
                    }
                ],
            }
        )

    evaluator_agent = EvaluatorAgent(
        contract_manager=cm,
        llm_client=_build_e2e_llm_client(judge_llm_transport),
    )

    def on_job_hired(
        job_id: int, provider_addr: str, eval_addr: str, amount_usd: float, task_desc: str
    ) -> dict[str, Any]:
        fulfill = provider_b.fulfill_job(job_id, task_desc)
        # Evaluator fetches deliverable over HTTP via on-chain dataUri and verifies keccak256 hash!
        verdict = evaluator_agent.evaluate_and_settle(
            job_id=job_id,
            task_requirement=task_desc,
            acceptance_criteria=["30 address flows", "Within 7 days"],
        )
        return {
            "deliverable": fetch_deliverable(fulfill["data_uri"]),
            "data_uri": fulfill["data_uri"],
            "evaluator_verdict": verdict["verdict"],
            "evaluator_score": verdict["score"],
        }

    def e2e_02_client_llm_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        msgs = body["messages"]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]
        tool_names_called = [m.get("name") for m in tool_msgs]

        if "probe_quote" not in tool_names_called:
            return 200, json.dumps(
                {
                    "id": "e2e02-1",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Probing quote for deep report.",
                                "tool_calls": [
                                    {
                                        "id": "c1",
                                        "type": "function",
                                        "function": {
                                            "name": "probe_quote",
                                            "arguments": json.dumps(
                                                {"resource_url": "http://provider-b.local/report"}
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if "pay_direct" not in tool_names_called:
            return 200, json.dumps(
                {
                    "id": "e2e02-2",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Trying pay_direct for 0.05 USDC.",
                                "tool_calls": [
                                    {
                                        "id": "c2",
                                        "type": "function",
                                        "function": {
                                            "name": "pay_direct",
                                            "arguments": json.dumps(
                                                {
                                                    "payee_address": provider_b_addr,
                                                    "amount_usd": 0.05,
                                                    "reason": "Direct purchase attempt",
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if "hire_escrow_job" not in tool_names_called:
            pay_obs = next(json.loads(m["content"]) for m in tool_msgs if m.get("name") == "pay_direct")
            assert pay_obs["ok"] is False
            return 200, json.dumps(
                {
                    "id": "e2e02-3",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "pay_direct was intercepted by on-chain per-tx cap. Switching to hire_escrow_job.",
                                "tool_calls": [
                                    {
                                        "id": "c3",
                                        "type": "function",
                                        "function": {
                                            "name": "hire_escrow_job",
                                            "arguments": json.dumps(
                                                {
                                                    "provider_address": provider_b_addr,
                                                    "evaluator_address": evaluator_addr,
                                                    "amount_usd": 0.05,
                                                    "duration_seconds": 3600,
                                                    "task_desc": "Deep laundering penetration report",
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if "inspect_job" not in tool_names_called:
            hire_obs = next(
                json.loads(m["content"]) for m in tool_msgs if m.get("name") == "hire_escrow_job"
            )
            return 200, json.dumps(
                {
                    "id": "e2e02-4",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Inspecting escrow job settlement.",
                                "tool_calls": [
                                    {
                                        "id": "c4",
                                        "type": "function",
                                        "function": {
                                            "name": "inspect_job",
                                            "arguments": json.dumps({"job_id": hire_obs["job_id"]}),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        inspect_obs = next(json.loads(m["content"]) for m in tool_msgs if m.get("name") == "inspect_job")
        return 200, json.dumps(
            {
                "id": "e2e02-5",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Escrow job completed. Finishing task.",
                            "tool_calls": [
                                {
                                    "id": "c5",
                                    "type": "function",
                                    "function": {
                                        "name": "finish_task",
                                        "arguments": json.dumps(
                                            {"final_report": inspect_obs["deliverable"]}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            }
        )

    try:
        toolbox = AgentToolbox(
            contract_manager=cm,
            on_job_hired_hook=on_job_hired,
            http_get=http_get_402,
        )
        client_agent = ClientAgent(
            llm_client=_build_e2e_llm_client(e2e_02_client_llm_transport),
            toolbox=toolbox,
            evaluator_address=evaluator_addr,
        )

        res = client_agent.run(
            user_goal=(
                "Acquire deep token laundering penetration analysis from http://provider-b.local/report. "
                "First probe_quote, then try pay_direct for 0.05 USDC first; when pay_direct reverts due to per-tx cap, "
                "switch to hire_escrow_job (duration_seconds=3600), call inspect_job, and finish_task with the report."
            ),
            market_resources=["http://provider-b.local/report"],
        )

        assert res["finished"] is True
        assert "30" in res["final_report"] or "addr_" in res["final_report"]
        # Verify on-chain state: job 1 is Completed, Provider B received 95% (47_500), Evaluator received 5% (2_500)
        job_info = cm.get_job(1)
        assert job_info["state"] == "Completed", f"Job 1 unexpectedly not Completed: {job_info}"
        assert job_info["data_uri"].startswith("http://127.0.0.1:")
        assert usdc_contract.functions.balanceOf(provider_b_addr).call() == 47_500
        assert usdc_contract.functions.balanceOf(evaluator_addr).call() == 2_500
        assert usdc_contract.functions.balanceOf(cm.vault_address).call() == 50_000
    finally:
        provider_b.close()


# ============================================================================
# E2E-03: Fraud Interception, On-Chain Refund & Provider Reselection
# ============================================================================


def test_e2e_03_fraud_reject_and_reselect_provider(anvil_env: dict[str, Any]) -> None:
    """E2E-03: Provider A (0.05) delivers garbage -> Evaluator rejects & refunds Vault (95% = 0.0475) ->
    ClientAgent observes refund, reselects Provider B (0.06) -> Evaluator completes job.
    Note: Total daily cap is 0.10 USDC. Without refund quota restoration, 0.05 + 0.06 = 0.11 > 0.10 would fail!
    """
    cm: ContractManager = anvil_env["cm"]
    usdc_contract = anvil_env["usdc_contract"]
    provider_a_addr: str = anvil_env["provider_a"]
    provider_b_addr: str = anvil_env["provider_b"]
    evaluator_addr: str = anvil_env["evaluator"]

    quote_a = encode_x402_header(
        {
            "price_usd": 0.05,
            "pay_to": provider_a_addr,
            "asset": cm.usdc_address,
            "type": "escrow",
            "description": "Budget Deep Report by Provider A",
        }
    )
    quote_b = encode_x402_header(
        {
            "price_usd": 0.06,
            "pay_to": provider_b_addr,
            "asset": cm.usdc_address,
            "type": "escrow",
            "description": "Premium Verified Deep Report by Provider B",
        }
    )

    def http_get_market(url: str, timeout: int) -> tuple[int, dict[str, str], str]:
        if "provider-a" in url:
            return 402, {"X-Payment-Required": quote_a}, '{"error": "Payment Required"}'
        return 402, {"X-Payment-Required": quote_b}, '{"error": "Payment Required"}'

    provider_a = ProviderAgent(
        name="ProviderA",
        address=provider_a_addr,
        private_key=PROVIDER_A_KEY,
        contract_manager=cm,
        deliverable_generator=lambda job_id, desc: "Stub report: only 1 address found, no timestamps.",
    )
    provider_b = ProviderAgent(
        name="ProviderB",
        address=provider_b_addr,
        private_key=PROVIDER_B_KEY,
        contract_manager=cm,
        deliverable_generator=lambda job_id, desc: _build_realistic_30_address_report(desc),
    )

    def judge_llm_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        user_content = body["messages"][-1]["content"]
        if "Stub report" in user_content:
            verdict_obj = {
                "verdict": "FAIL",
                "score": 15,
                "reasons": ["Deliverable missing required 30 address flows and timestamps"],
            }
        else:
            verdict_obj = {
                "verdict": "PASS",
                "score": 96,
                "reasons": ["Deliverable contains all 30 address flows and full fields"],
            }
        return 200, json.dumps(
            {
                "id": "judge-e2e03",
                "choices": [{"message": {"role": "assistant", "content": json.dumps(verdict_obj)}}],
            }
        )

    evaluator_agent = EvaluatorAgent(
        contract_manager=cm,
        llm_client=_build_e2e_llm_client(judge_llm_transport),
    )

    def on_job_hired(
        job_id: int, provider_addr: str, eval_addr: str, amount_usd: float, task_desc: str
    ) -> dict[str, Any]:
        if Web3.to_checksum_address(provider_addr) == Web3.to_checksum_address(provider_a_addr):
            fulfill = provider_a.fulfill_job(job_id, task_desc)
        else:
            fulfill = provider_b.fulfill_job(job_id, task_desc)

        # Evaluator fetches deliverable over HTTP via on-chain dataUri and verifies keccak256 hash!
        verdict = evaluator_agent.evaluate_and_settle(
            job_id=job_id,
            task_requirement=task_desc,
            acceptance_criteria=["Must include 30 address flows", "Full fields", "Within 7 days"],
        )
        return {
            "deliverable": fetch_deliverable(fulfill["data_uri"]),
            "data_uri": fulfill["data_uri"],
            "evaluator_verdict": verdict["verdict"],
            "evaluator_score": verdict["score"],
            "evaluator_reasons": verdict["reasons"],
        }

    def e2e_03_client_llm_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        msgs = body["messages"]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]

        if not tool_msgs:
            return 200, json.dumps(
                {
                    "id": "e2e03-1",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Checking vault status and probing quotes from Provider A and Provider B.",
                                "tool_calls": [
                                    {
                                        "id": "call_status",
                                        "type": "function",
                                        "function": {"name": "get_vault_status", "arguments": "{}"},
                                    },
                                    {
                                        "id": "call_probe_a",
                                        "type": "function",
                                        "function": {
                                            "name": "probe_quote",
                                            "arguments": json.dumps(
                                                {"resource_url": "http://provider-a.local/deep"}
                                            ),
                                        },
                                    },
                                    {
                                        "id": "call_probe_b",
                                        "type": "function",
                                        "function": {
                                            "name": "probe_quote",
                                            "arguments": json.dumps(
                                                {"resource_url": "http://provider-b.local/deep"}
                                            ),
                                        },
                                    },
                                ],
                            }
                        }
                    ],
                }
            )

        hire_msgs = [m for m in tool_msgs if m.get("name") == "hire_escrow_job"]
        inspect_msgs = [m for m in tool_msgs if m.get("name") == "inspect_job"]

        if len(hire_msgs) == 0:
            return 200, json.dumps(
                {
                    "id": "e2e03-2",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Provider A is cheaper at 0.05 USDC (> 0.01 direct cap). Hiring Provider A via escrow.",
                                "tool_calls": [
                                    {
                                        "id": "call_hire_a",
                                        "type": "function",
                                        "function": {
                                            "name": "hire_escrow_job",
                                            "arguments": json.dumps(
                                                {
                                                    "provider_address": provider_a_addr,
                                                    "evaluator_address": evaluator_addr,
                                                    "amount_usd": 0.05,
                                                    "duration_seconds": 3600,
                                                    "task_desc": "30-address laundering report",
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if len(hire_msgs) == 1 and len(inspect_msgs) == 0:
            job1_id = json.loads(hire_msgs[0]["content"])["job_id"]
            return 200, json.dumps(
                {
                    "id": "e2e03-3",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": f"Inspecting Job {job1_id} with Provider A.",
                                "tool_calls": [
                                    {
                                        "id": "call_inspect_1",
                                        "type": "function",
                                        "function": {
                                            "name": "inspect_job",
                                            "arguments": json.dumps({"job_id": job1_id}),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if len(hire_msgs) == 1 and len(inspect_msgs) == 1:
            job1_obs = json.loads(inspect_msgs[0]["content"])
            assert job1_obs["state"] == "Rejected"
            return 200, json.dumps(
                {
                    "id": "e2e03-4",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Job 1 was Rejected by Evaluator due to missing 30 address flows, "
                                    "and 0.0475 USDC was refunded to AgentVault. Switching to Provider B (0.06 USDC)."
                                ),
                                "tool_calls": [
                                    {
                                        "id": "call_hire_b",
                                        "type": "function",
                                        "function": {
                                            "name": "hire_escrow_job",
                                            "arguments": json.dumps(
                                                {
                                                    "provider_address": provider_b_addr,
                                                    "evaluator_address": evaluator_addr,
                                                    "amount_usd": 0.06,
                                                    "duration_seconds": 3600,
                                                    "task_desc": "30-address laundering report (Provider B)",
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        if len(hire_msgs) == 2 and len(inspect_msgs) == 1:
            job2_id = json.loads(hire_msgs[1]["content"])["job_id"]
            return 200, json.dumps(
                {
                    "id": "e2e03-5",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": f"Inspecting Job {job2_id} with Provider B.",
                                "tool_calls": [
                                    {
                                        "id": "call_inspect_2",
                                        "type": "function",
                                        "function": {
                                            "name": "inspect_job",
                                            "arguments": json.dumps({"job_id": job2_id}),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

        job2_obs = json.loads(inspect_msgs[1]["content"])
        assert job2_obs["state"] == "Completed"
        return 200, json.dumps(
            {
                "id": "e2e03-6",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Job 2 with Provider B passed inspection and settled. Finishing task.",
                            "tool_calls": [
                                {
                                    "id": "call_finish",
                                    "type": "function",
                                    "function": {
                                        "name": "finish_task",
                                        "arguments": json.dumps(
                                            {"final_report": job2_obs["deliverable"]}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            }
        )

    try:
        toolbox = AgentToolbox(
            contract_manager=cm,
            on_job_hired_hook=on_job_hired,
            http_get=http_get_market,
        )
        client_agent = ClientAgent(
            llm_client=_build_e2e_llm_client(e2e_03_client_llm_transport),
            toolbox=toolbox,
            evaluator_address=evaluator_addr,
        )

        res = client_agent.run(
            user_goal=(
                "Produce a deep laundering and fund penetration report within 0.10 USDC budget. "
                "First probe both http://provider-a.local/deep and http://provider-b.local/deep. "
                "Hire the cheaper Provider A (0.05 USDC) via hire_escrow_job (duration_seconds=3600) and call inspect_job. "
                "When Job 1 is Rejected and refunded, hire Provider B (0.06 USDC) via hire_escrow_job (duration_seconds=3600), "
                "call inspect_job on Job 2, and call finish_task with Provider B's verified 30-address report."
            ),
            market_resources=[
                "http://provider-a.local/deep",
                "http://provider-b.local/deep",
            ],
        )

        assert res["finished"] is True
        assert "30" in res["final_report"] or "Flow" in res["final_report"] or "laundering" in res["final_report"].lower()

        # Verify on-chain state & balances with 5% evaluatorFeeBps:
        # Job 1 (50_000) -> Rejected: Provider A got 0, Evaluator got 2_500 fee, Vault refunded 47_500
        # Job 2 (60_000) -> Completed: Provider B got 57_000 (95%), Evaluator got 3_000 fee (total 5_500)
        # Vault remaining balance -> 100_000 - 50_000 + 47_500 - 60_000 = 37_500 units
        assert cm.get_job(1)["state"] == "Rejected"
        assert cm.get_job(2)["state"] == "Completed"
        assert usdc_contract.functions.balanceOf(provider_a_addr).call() == 0
        assert usdc_contract.functions.balanceOf(provider_b_addr).call() == 57_000
        assert usdc_contract.functions.balanceOf(evaluator_addr).call() == 5_500
        assert usdc_contract.functions.balanceOf(cm.vault_address).call() == 37_500
    finally:
        provider_a.close()
        provider_b.close()


# ============================================================================
# E2E-04: Tampered HTTP Deliverable Rejection & Submitted-State Evaluator Timeout
# ============================================================================


def test_e2e_04_evaluation_timeout_and_tampered_data_uri(anvil_env: dict[str, Any]) -> None:
    """A5 (E2E-04):
    1. Provider A submits resultHash + dataUri on-chain, then tampers with the hosted HTTP body ->
       EvaluatorAgent detects keccak256 mismatch and calls rejectJob on-chain without calling LLM.
    2. Provider B submits resultHash + dataUri on-chain (state=Submitted), then Evaluator goes offline ->
       After evaluationDeadline (3600s), Client claims evaluation timeout via claimEvaluationTimeout ->
       100% of job.amount is refunded to AgentVault and daily spend quota is restored.
    """
    w3: Web3 = anvil_env["w3"]
    cm: ContractManager = anvil_env["cm"]
    usdc_contract = anvil_env["usdc_contract"]
    provider_a_addr: str = anvil_env["provider_a"]
    provider_b_addr: str = anvil_env["provider_b"]
    evaluator_addr: str = anvil_env["evaluator"]

    provider_a = ProviderAgent(
        name="ProviderA",
        address=provider_a_addr,
        private_key=PROVIDER_A_KEY,
        contract_manager=cm,
        mode="honest",
    )
    provider_b = ProviderAgent(
        name="ProviderB",
        address=provider_b_addr,
        private_key=PROVIDER_B_KEY,
        contract_manager=cm,
        mode="honest",
    )

    llm_called = {"count": 0}

    def should_not_be_called_transport(
        url: str, headers: dict[str, str], body: dict[str, Any], timeout: int
    ) -> tuple[int, str]:
        llm_called["count"] += 1
        return 200, '{"choices": [{"message": {"content": "{}"}}]}'

    offline_cfg = LLMConfig(
        api_key="sk-no-call",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        client_model="gpt-4o-mini",
        evaluator_model="gpt-4o-mini",
        temperature=0.0,
        timeout_seconds=5,
    )
    evaluator_agent = EvaluatorAgent(
        contract_manager=cm,
        llm_client=LLMClient(offline_cfg, transport=should_not_be_called_transport),
    )

    try:
        # Part 1: Fund Job 1 (50_000 USDC), Provider A submits valid hash + dataUri, then tampers with HTTP payload
        fund1 = cm.fund_job(provider_a_addr, evaluator_addr, 50_000, 3600)
        job1_id = fund1["job_id"]
        provider_a.fulfill_job(job1_id, "30-address flow trace")
        provider_a.tamper_hosted_deliverable(job1_id, "MALICIOUS_TAMPERED_OFFCHAIN_CONTENT")

        settle1 = evaluator_agent.evaluate_and_settle(
            job_id=job1_id,
            task_requirement="30-address flow trace",
            acceptance_criteria=["30 address flows"],
        )
        assert settle1["verdict"] == "FAIL"
        assert settle1["action"] == "rejectJob"
        assert "hash mismatch" in settle1["rejection_reason"].lower()
        assert llm_called["count"] == 0
        assert cm.get_job(job1_id)["state"] == "Rejected"
        # Evaluator received 2_500 fee for rejecting tampered job; Vault received 47_500 refund
        assert usdc_contract.functions.balanceOf(evaluator_addr).call() == 2_500
        assert usdc_contract.functions.balanceOf(cm.vault_address).call() == 97_500

        # Part 2: Fund Job 2 (50_000 USDC), Provider B submits result (state=Submitted), Evaluator goes offline
        fund2 = cm.fund_job(provider_b_addr, evaluator_addr, 50_000, 3600)
        job2_id = fund2["job_id"]
        provider_b.fulfill_job(job2_id, "30-address flow trace")

        job2_sub = cm.get_job(job2_id)
        assert job2_sub["state"] == "Submitted"
        assert job2_sub["evaluation_deadline"] > 0

        # Before evaluation_deadline: claim_evaluation_timeout must revert
        with pytest.raises( Exception ):
            cm.claim_evaluation_timeout(job2_id)

        # Advance Anvil EVM time past evaluationPeriod (3600s + 10s)
        w3.provider.make_request("evm_increaseTime", [3610])  # type: ignore[arg-type]
        w3.provider.make_request("evm_mine", [])  # type: ignore[arg-type]

        # Now claim_evaluation_timeout succeeds and refunds 100% of Job 2 (50_000) to AgentVault
        timeout_res = cm.claim_evaluation_timeout(job2_id)
        assert timeout_res["state"] == "Expired"
        assert cm.get_job(job2_id)["state"] == "Expired"
        assert usdc_contract.functions.balanceOf(cm.vault_address).call() == 97_500
        assert cm.get_vault_status()["daily_spend_counter_usd"] == 0.0025
    finally:
        provider_a.close()
        provider_b.close()
