"""Provider Agent that hosts deliverables over HTTP and submits resultHash + dataUri on-chain."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from eth_account import Account
from web3 import Web3

from agent_runtime.contracts import ContractManager
from agent_runtime.x402 import (
    encrypt_deliverable_ecies,
    register_local_http_handler,
    unregister_local_http_handler,
)


class PersistentDeliverableStore:
    """Content-addressed persistent store for job deliverables across process restarts."""

    def __init__(self, root_dir: str | Path) -> None:
        self._root = Path(root_dir)
        self._objects_dir = self._root / "objects"
        self._jobs_dir = self._root / "jobs"
        self._objects_dir.mkdir(parents=True, exist_ok=True)
        self._jobs_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _atomic_write_text(target: Path, content: str) -> None:
        fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=".tmp_", suffix=".part")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, target)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise

    def put(self, job_id: int, payload: str) -> str:
        """Persist payload by SHA-256 content address and link job_id -> cid atomically."""
        cid = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        blob_path = self._objects_dir / f"{cid}.blob"
        if not blob_path.exists():
            self._atomic_write_text(blob_path, payload)
        job_meta = json.dumps({"job_id": int(job_id), "cid": cid}, ensure_ascii=False)
        self._atomic_write_text(self._jobs_dir / f"{int(job_id)}.json", job_meta)
        return cid

    def get(self, job_id: int) -> str | None:
        """Load persisted payload for job_id from disk, returning None if absent."""
        meta_path = self._jobs_dir / f"{int(job_id)}.json"
        if not meta_path.is_file():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        cid = str(meta.get("cid", ""))
        blob_path = self._objects_dir / f"{cid}.blob"
        if not blob_path.is_file():
            return None
        return blob_path.read_text(encoding="utf-8")

    def contains(self, job_id: int) -> bool:
        return self.get(job_id) is not None


def _default_deliverable_for_mode(mode: str, job_id: int, task_desc: str) -> str:
    if mode == "fraud":
        return f"Job #{job_id} quick summary: 2 addresses checked (0x11..11 -> 0x22..22). No issues found."
    rows = [
        f"Flow #{i:02d} | tx_hash=0x{i:064x} | from=0x{i:040x} | to=0x{(i + 100):040x} | amount={(i * 1250)}.00 USDC | hop={i % 4 + 1} | age={(i % 6) + 1} days ago (within 7 days) | risk=HIGH"
        for i in range(1, 31)
    ]
    return (
        f" Comprehensive 30-Address Fund Penetration Report for Job #{job_id}\n"
        f"Task: {task_desc}\n"
        + "\n".join(rows)
    )


class ProviderAgent:
    """Independent Provider Agent that hosts deliverables over HTTP and submits resultHash + dataUri."""

    def __init__(
        self,
        name: str,
        private_key: str,
        contract_manager: ContractManager,
        address: str | None = None,
        deliverable_generator: Callable[[int, str], str] | None = None,
        mode: str = "honest",
        recipient_pubkeys: list[str] | None = None,
        require_encryption: bool = False,
        storage_dir: str | Path | None = None,
        listen_port: int = 0,
    ) -> None:
        self._name = name
        self._private_key = private_key
        derived_addr = address or Account.from_key(private_key).address
        self._address = Web3.to_checksum_address(derived_addr)
        self._cm = contract_manager
        self._mode = mode
        self._recipient_pubkeys = list(recipient_pubkeys) if recipient_pubkeys else []
        self._require_encryption = bool(require_encryption)
        self._generator = deliverable_generator or (
            lambda jid, desc: _default_deliverable_for_mode(self._mode, jid, desc)
        )
        self._store = PersistentDeliverableStore(storage_dir) if storage_dir is not None else None
        self._hosted_deliverables: dict[int, str] = {}
        self._listen_port = int(listen_port)
        self._server: ThreadingHTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._base_url: str = ""
        self._start_http_server()

    def _get_deliverable(self, job_id: int) -> str | None:
        if job_id in self._hosted_deliverables:
            return self._hosted_deliverables[job_id]
        if self._store is not None:
            return self._store.get(job_id)
        return None

    def _save_deliverable(self, job_id: int, payload: str) -> None:
        self._hosted_deliverables[int(job_id)] = payload
        if self._store is not None:
            self._store.put(int(job_id), payload)

    def _handle_http_path(self, path: str) -> tuple[int, dict[str, str], str]:
        prefix = "/deliverables/"
        if path.startswith(prefix):
            try:
                jid = int(path[len(prefix) :].split("?")[0])
            except ValueError:
                return 400, {}, "Bad Request"
            body = self._get_deliverable(jid)
            if body is not None:
                return (
                    200,
                    {"Content-Type": "text/plain; charset=utf-8"},
                    body,
                )
        return 404, {}, "Not Found"

    def _start_http_server(self) -> None:
        provider_self = self

        class DeliverableHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                status, headers, body_str = provider_self._handle_http_path(self.path)
                body = body_str.encode("utf-8")
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if status == 200:
                    self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:
                return

        try:
            self._server = ThreadingHTTPServer(("127.0.0.1", self._listen_port), DeliverableHandler)
            port = self._server.server_address[1]
            self._base_url = f"http://127.0.0.1:{port}"
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._server_thread.start()
        except OSError:
            self._server = None
            fallback_port = self._listen_port if self._listen_port > 0 else (18900 + (id(self) % 1000))
            self._base_url = f"http://127.0.0.1:{fallback_port}"

        register_local_http_handler(self._base_url, self._handle_http_path)

    def close(self) -> None:
        """Stop the local deliverable HTTP server."""
        if self._base_url:
            unregister_local_http_handler(self._base_url)
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def tamper_hosted_deliverable(self, job_id: int, new_content: str) -> None:
        """Mutate the hosted HTTP deliverable after on-chain hash commitment (for tamper tests)."""
        self._save_deliverable(int(job_id), new_content)

    def _resolve_recipient_pubkeys(self, job_id: int, job_info: dict[str, Any] | None) -> list[str]:
        if self._recipient_pubkeys:
            return list(self._recipient_pubkeys)
        if job_info is None or not hasattr(self._cm, "get_encryption_public_key"):
            if self._require_encryption:
                raise ValueError(f"Missing on-chain encryption public key registry for job {job_id}")
            return []

        pubkeys: list[str] = []
        missing_roles: list[str] = []
        for role in ("client", "evaluator"):
            addr = str(job_info.get(role, "")).strip()
            if not addr:
                missing_roles.append(f"{role}(unknown)")
                continue
            pk = str(self._cm.get_encryption_public_key(addr) or "").strip()
            if pk:
                if pk not in pubkeys:
                    pubkeys.append(pk)
            else:
                missing_roles.append(f"{role}({addr})")

        if self._require_encryption and missing_roles:
            raise ValueError(
                f"Missing on-chain encryption public key for job {job_id}: {', '.join(missing_roles)}"
            )
        if missing_roles:
            return []
        return pubkeys

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    def fulfill_job(self, job_id: int, task_desc: str) -> dict[str, Any]:
        """Verify job is Funded (when available), host deliverable via HTTP, and call submitResult."""
        job_info: dict[str, Any] | None = None
        if hasattr(self._cm, "get_job"):
            try:
                job_info = self._cm.get_job(job_id)
                if "state" in job_info and job_info["state"] != "Funded":
                    raise RuntimeError(
                        f"Provider {self._name} refuses job {job_id}: expected state Funded, got {job_info['state']}"
                    )
                if "provider" in job_info and Web3.to_checksum_address(job_info["provider"]) != self._address:
                    raise RuntimeError(
                        f"Provider {self._name} ({self._address}) is not assigned to job {job_id} ({job_info['provider']})"
                    )
            except KeyError:
                job_info = None

        deliverable_text = self._generator(job_id, task_desc)
        pubkeys = self._resolve_recipient_pubkeys(job_id, job_info)
        if pubkeys:
            hosted_payload = encrypt_deliverable_ecies(deliverable_text, pubkeys)
        else:
            hosted_payload = deliverable_text
        self._save_deliverable(int(job_id), hosted_payload)
        data_uri = f"{self._base_url}/deliverables/{int(job_id)}"
        result_hash: bytes = Web3.keccak(text=hosted_payload)

        sig = inspect.signature(self._cm.submit_result)
        if "result_hash" in sig.parameters:
            tx_res = self._cm.submit_result(
                job_id=job_id,
                result_hash=result_hash,
                provider_private_key=self._private_key,
                data_uri=data_uri,
            )
        else:
            tx_res = self._cm.submit_result(
                job_id=job_id,
                deliverable_text=hosted_payload,
                provider_private_key=self._private_key,
                data_uri=data_uri,
            )

        return {
            "job_id": job_id,
            "provider": self._address,
            "deliverable": deliverable_text,
            "hosted_payload": hosted_payload,
            "encrypted": bool(pubkeys),
            "data_uri": data_uri,
            "result_hash": tx_res["result_hash"],
            "tx_hash": tx_res["tx_hash"],
        }

    def submit_for_job(self, job_id: int, task_desc: str) -> dict[str, Any]:
        """Alias for fulfill_job used by HTTP dataUri handshake tests."""
        return self.fulfill_job(job_id=job_id, task_desc=task_desc)
