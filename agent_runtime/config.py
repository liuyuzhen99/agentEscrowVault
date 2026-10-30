"""Configuration loader for AgentEscrowVault LLM and blockchain runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for OpenAI-compatible LLM inference (Client & Evaluator agents)."""

    api_key: str
    base_url: str
    model: str
    client_model: str
    evaluator_model: str
    temperature: float
    timeout_seconds: int


@dataclass(frozen=True)
class AgentRuntimeConfig:
    """Unified configuration for LLM agents and Base Sepolia / EVM contracts."""

    llm: LLMConfig
    rpc_url: str
    chain_id: int
    usdc_address: str
    vault_address: str
    escrow_address: str
    owner_private_key: str
    agent_session_private_key: str
    evaluator_private_key: str


def load_config(
    env_path: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> AgentRuntimeConfig:
    """Load AgentRuntimeConfig from optional .env file and environment mapping at call time."""
    merged: dict[str, str] = {}
    target_path = Path(env_path) if env_path is not None else Path(".env")
    if target_path.is_file():
        file_vals = dotenv_values(target_path)
        for k, v in file_vals.items():
            if v is not None:
                merged[k] = v

    env_source = environ if environ is not None else os.environ
    for k, v in env_source.items():
        merged[k] = v

    default_model = merged.get("LLM_MODEL", "gpt-4o-mini")
    llm_cfg = LLMConfig(
        api_key=merged.get("LLM_API_KEY", ""),
        base_url=merged.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        model=default_model,
        client_model=merged.get("CLIENT_LLM_MODEL", default_model),
        evaluator_model=merged.get("EVALUATOR_LLM_MODEL", default_model),
        temperature=float(merged.get("LLM_TEMPERATURE", "0.0")),
        timeout_seconds=int(merged.get("LLM_TIMEOUT_SECONDS", "60")),
    )

    return AgentRuntimeConfig(
        llm=llm_cfg,
        rpc_url=merged.get("RPC_URL", "https://sepolia.base.org"),
        chain_id=int(merged.get("CHAIN_ID", "84532")),
        usdc_address=merged.get(
            "USDC_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
        ),
        vault_address=merged.get(
            "VAULT_ADDRESS", "0x0000000000000000000000000000000000000000"
        ),
        escrow_address=merged.get(
            "ESCROW_ADDRESS", "0x0000000000000000000000000000000000000000"
        ),
        owner_private_key=merged.get("OWNER_PRIVATE_KEY", ""),
        agent_session_private_key=merged.get("AGENT_SESSION_PRIVATE_KEY", ""),
        evaluator_private_key=merged.get("EVALUATOR_PRIVATE_KEY", ""),
    )
