"""HTTP 402 Payment Required header encoder/decoder, quote probe, ECIES encryption, and deliverable fetcher."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Callable
from urllib.parse import urlparse

import requests
from eth_keys import keys
from eth_keys.backends.native.ecdsa import (
    decode_public_key,
    encode_raw_public_key,
    fast_multiply,
)

# Registry of local loopback HTTP handlers (`http://127.0.0.1:<port>`) used as a
# fallback only when OS sandbox restrictions (EPERM) block loopback TCP connect().
_LOCAL_HTTP_HANDLERS: dict[str, Callable[[str], tuple[int, dict[str, str], str]]] = {}


def register_local_http_handler(
    base_url: str, handler: Callable[[str], tuple[int, dict[str, str], str]]
) -> None:
    """Register a local HTTP handler for a base_url (e.g. http://127.0.0.1:50123)."""
    _LOCAL_HTTP_HANDLERS[base_url.rstrip("/")] = handler


def unregister_local_http_handler(base_url: str) -> None:
    """Unregister a local HTTP handler."""
    _LOCAL_HTTP_HANDLERS.pop(base_url.rstrip("/"), None)


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


def fetch_deliverable(
    data_uri: str,
    timeout: int = 10,
    http_get: Callable[[str, int], tuple[int, dict[str, str], str]] | None = None,
) -> str:
    """Download provider deliverable content from an HTTP(S) dataUri endpoint."""
    if not data_uri or not data_uri.startswith(("http://", "https://")):
        raise ValueError(f"Unsupported or empty deliverable dataUri: {data_uri!r}")

    if http_get is not None:
        status_code, _, body = http_get(data_uri, timeout)
    else:
        try:
            resp = requests.get(data_uri, timeout=timeout)
            status_code = resp.status_code
            body = resp.text
        except requests.RequestException as exc:
            parsed = urlparse(data_uri)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            local_handler = _LOCAL_HTTP_HANDLERS.get(base_url)
            if local_handler is not None:
                status_code, _, body = local_handler(parsed.path or "/")
            else:
                raise RuntimeError(f"Failed to fetch deliverable from {data_uri}: {exc}") from exc

    if status_code != 200:
        raise RuntimeError(f"Failed to fetch deliverable from {data_uri}: HTTP {status_code}")
    return body


ECIES_SCHEME = "secp256k1-ecies-v1"


def _normalize_private_key_bytes(private_key_hex: str) -> bytes:
    clean = private_key_hex.strip().removeprefix("0x").removeprefix("0X")
    raw = bytes.fromhex(clean)
    if len(raw) != 32:
        raise ValueError(f"Expected 32-byte secp256k1 private key, got {len(raw)} bytes")
    return raw


def _normalize_pubkey_bytes(pubkey_hex: str) -> bytes:
    clean = pubkey_hex.strip().removeprefix("0x").removeprefix("0X")
    raw = bytes.fromhex(clean)
    if len(raw) == 65 and raw[0] == 0x04:
        raw = raw[1:]
    if len(raw) != 64:
        raise ValueError(f"Expected 64-byte uncompressed secp256k1 public key, got {len(raw)} bytes")
    # Validate point lies on secp256k1 curve
    decode_public_key(raw)
    return raw


def derive_public_key_hex(private_key_hex: str) -> str:
    """Derive 64-byte uncompressed secp256k1 public key hex ('0x' + 128 hex chars) from private key."""
    sk_bytes = _normalize_private_key_bytes(private_key_hex)
    pub_bytes = keys.PrivateKey(sk_bytes).public_key.to_bytes()
    return "0x" + pub_bytes.hex()


def _ecdh_shared_secret(private_key_bytes: bytes, peer_pubkey_bytes: bytes) -> bytes:
    scalar = int.from_bytes(private_key_bytes, "big")
    point = decode_public_key(peer_pubkey_bytes)
    shared_point = encode_raw_public_key(fast_multiply(point, scalar))
    return hashlib.sha256(b"secp256k1-ecies-v1-ecdh:" + shared_point).digest()


def _stream_xor_sha256(enc_key: bytes, iv: bytes, data: bytes) -> bytes:
    out = bytearray(len(data))
    block_count = (len(data) + 31) // 32
    for counter in range(block_count):
        keystream = hashlib.sha256(enc_key + iv + counter.to_bytes(8, "big")).digest()
        start = counter * 32
        end = min(start + 32, len(data))
        for idx in range(start, end):
            out[idx] = data[idx] ^ keystream[idx - start]
    return bytes(out)


def encrypt_deliverable_ecies(plaintext: str, recipient_pubkeys: list[str]) -> str:
    """Encrypt deliverable plaintext for one or more secp256k1 recipient public keys (ECIES)."""
    if not recipient_pubkeys:
        raise ValueError("recipient_pubkeys must contain at least one recipient public key")

    plaintext_bytes = plaintext.encode("utf-8")
    cek = secrets.token_bytes(32)
    content_iv = secrets.token_bytes(16)
    content_enc_key = hmac.new(cek, b"ecies-content-enc", hashlib.sha256).digest()
    content_mac_key = hmac.new(cek, b"ecies-content-mac", hashlib.sha256).digest()

    ciphertext = _stream_xor_sha256(content_enc_key, content_iv, plaintext_bytes)
    content_tag = hmac.new(content_mac_key, content_iv + ciphertext, hashlib.sha256).digest()

    recipients_entries: list[dict[str, str]] = []
    seen_pubkeys: set[str] = set()
    for pub_hex in recipient_pubkeys:
        pub_bytes = _normalize_pubkey_bytes(pub_hex)
        norm_pub_hex = "0x" + pub_bytes.hex()
        if norm_pub_hex in seen_pubkeys:
            continue
        seen_pubkeys.add(norm_pub_hex)

        eph_sk_bytes = secrets.token_bytes(32)
        eph_pub_bytes = keys.PrivateKey(eph_sk_bytes).public_key.to_bytes()
        shared = _ecdh_shared_secret(eph_sk_bytes, pub_bytes)
        wrap_enc_key = hmac.new(shared, b"ecies-wrap-enc", hashlib.sha256).digest()
        wrap_mac_key = hmac.new(shared, b"ecies-wrap-mac", hashlib.sha256).digest()
        wrap_iv = secrets.token_bytes(16)
        enc_cek = _stream_xor_sha256(wrap_enc_key, wrap_iv, cek)
        wrap_mac = hmac.new(
            wrap_mac_key, eph_pub_bytes + wrap_iv + enc_cek, hashlib.sha256
        ).digest()

        recipients_entries.append(
            {
                "recipient_pubkey": norm_pub_hex,
                "ephemeral_pubkey": "0x" + eph_pub_bytes.hex(),
                "iv": wrap_iv.hex(),
                "encrypted_key": enc_cek.hex(),
                "mac": wrap_mac.hex(),
            }
        )

    envelope = {
        "scheme": ECIES_SCHEME,
        "iv": content_iv.hex(),
        "ciphertext": ciphertext.hex(),
        "tag": content_tag.hex(),
        "recipients": recipients_entries,
    }
    return json.dumps(envelope, separators=(",", ":"))


def decrypt_deliverable_ecies(payload: str, private_key_hex: str) -> str:
    """Decrypt a secp256k1-ecies-v1 deliverable envelope using an authorized recipient's private key."""
    stripped = payload.strip()
    if not stripped.startswith("{"):
        return payload
    try:
        envelope = json.loads(stripped)
    except Exception:
        return payload

    if not isinstance(envelope, dict) or envelope.get("scheme") != ECIES_SCHEME:
        return payload

    if not private_key_hex:
        raise PermissionError("Private key required to decrypt ECIES deliverable: caller is not an authorized recipient")

    sk_bytes = _normalize_private_key_bytes(private_key_hex)
    my_pub_hex = ("0x" + keys.PrivateKey(sk_bytes).public_key.to_bytes().hex()).lower()

    recipients = envelope.get("recipients")
    if not isinstance(recipients, list):
        raise ValueError("Malformed ECIES envelope: missing recipients list")

    matched_entry: dict[str, Any] | None = None
    for entry in recipients:
        if isinstance(entry, dict) and str(entry.get("recipient_pubkey", "")).lower() == my_pub_hex:
            matched_entry = entry
            break

    if matched_entry is None:
        raise PermissionError(
            f"Public key {my_pub_hex} is not an authorized recipient of this ECIES deliverable"
        )

    eph_pub_bytes = _normalize_pubkey_bytes(str(matched_entry["ephemeral_pubkey"]))
    wrap_iv = bytes.fromhex(str(matched_entry["iv"]))
    enc_cek = bytes.fromhex(str(matched_entry["encrypted_key"]))
    expected_wrap_mac = bytes.fromhex(str(matched_entry["mac"]))

    shared = _ecdh_shared_secret(sk_bytes, eph_pub_bytes)
    wrap_enc_key = hmac.new(shared, b"ecies-wrap-enc", hashlib.sha256).digest()
    wrap_mac_key = hmac.new(shared, b"ecies-wrap-mac", hashlib.sha256).digest()
    computed_wrap_mac = hmac.new(
        wrap_mac_key, eph_pub_bytes + wrap_iv + enc_cek, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(computed_wrap_mac, expected_wrap_mac):
        raise ValueError("ECIES key wrap MAC verification failed")

    cek = _stream_xor_sha256(wrap_enc_key, wrap_iv, enc_cek)

    content_iv = bytes.fromhex(str(envelope["iv"]))
    ciphertext = bytes.fromhex(str(envelope["ciphertext"]))
    expected_content_tag = bytes.fromhex(str(envelope["tag"]))

    content_enc_key = hmac.new(cek, b"ecies-content-enc", hashlib.sha256).digest()
    content_mac_key = hmac.new(cek, b"ecies-content-mac", hashlib.sha256).digest()
    computed_content_tag = hmac.new(
        content_mac_key, content_iv + ciphertext, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(computed_content_tag, expected_content_tag):
        raise ValueError("ECIES content MAC verification failed")

    plaintext_bytes = _stream_xor_sha256(content_enc_key, content_iv, ciphertext)
    return plaintext_bytes.decode("utf-8")

