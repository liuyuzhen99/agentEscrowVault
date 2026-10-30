"""HTTP 402 Payment Required header encoder/decoder and quote probe."""

from __future__ import annotations

import base64
import json
from typing import Any, Callable

import requests


def encode_x402_header(requirement: dict[str, Any]) -> str:
    """Encode an x402 payment requirement dict as a Base64 header string."""
    raw_bytes = json.dumps(requirement, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw_bytes).decode("ascii")


def decode_x402_header(encoded_header: str) -> dict[str, Any]:
    """Decode a Base64-encoded x402 payment requirement header into a dict."""
    try:
        raw_bytes = base64.b64decode(encoded_header.strip(), validate=True)
        parsed = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid Base64 x402 payment header: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Decoded x402 header must be a JSON object")

    for required in ("price_usd", "pay_to", "asset", "type"):
        if required not in parsed:
            raise ValueError(f"Decoded x402 header missing required field '{required}'")
    return parsed


def probe_quote(
    resource_url: str,
    timeout: int = 10,
    http_get: Callable[[str, int], tuple[int, dict[str, str], str]] | None = None,
) -> dict[str, Any]:
    """Send an unauthenticated GET request to capture 402 Payment Required quote details."""
    if http_get is not None:
        status_code, headers, _ = http_get(resource_url, timeout)
    else:
        resp = requests.get(resource_url, timeout=timeout)
        status_code = resp.status_code
        headers = dict(resp.headers)

    if status_code != 402:
        return {
            "status_code": status_code,
            "resource_url": resource_url,
            "error": f"Expected HTTP 402 Payment Required, got {status_code}",
        }

    lower_headers = {str(k).lower(): v for k, v in headers.items()}
    header_val = (
        lower_headers.get("x-payment-required")
        or lower_headers.get("www-authenticate")
        or lower_headers.get("payment-required")
    )
    if not header_val:
        raise ValueError(f"HTTP 402 response from {resource_url} missing payment header")

    if header_val.lower().startswith("x402 "):
        header_val = header_val[5:].strip()

    decoded = decode_x402_header(header_val)
    return {
        "status_code": 402,
        "resource_url": resource_url,
        "price_usd": float(decoded["price_usd"]),
        "pay_to": str(decoded["pay_to"]),
        "asset": str(decoded["asset"]),
        "type": str(decoded["type"]),
        "description": str(decoded.get("description", "")),
        "deliverable_endpoint": str(decoded.get("deliverable_endpoint", resource_url)),
    }
