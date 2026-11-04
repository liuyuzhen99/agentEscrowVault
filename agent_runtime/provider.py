"""Provider Agent that hosts deliverables over HTTP and submits resultHash + dataUri on-chain."""

from __future__ import annotations

import inspect
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from eth_account import Account
from web3 import Web3

from agent_runtime.contracts import ContractManager
from agent_runtime.x402 import register_local_http_handler, unregister_local_http_handler


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
    ) -> None:
        self._name = name
        self._private_key = private_key
        derived_addr = address or Account.from_key(private_key).address
        self._address = Web3.to_checksum_address(derived_addr)
        self._cm = contract_manager
        self._mode = mode
        self._generator = deliverable_generator or (
            lambda jid, desc: _default_deliverable_for_mode(self._mode, jid, desc)
        )
        self._hosted_deliverables: dict[int, str] = {}
        self._server: ThreadingHTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._base_url: str = ""
        self._start_http_server()

    def _handle_http_path(self, path: str) -> tuple[int, dict[str, str], str]:
        prefix = "/deliverables/"
        if path.startswith(prefix):
            try:
                jid = int(path[len(prefix) :].split("?")[0])
            except ValueError:
                return 400, {}, "Bad Request"
            if jid in self._hosted_deliverables:
                body = self._hosted_deliverables[jid]
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
            self._server = ThreadingHTTPServer(("127.0.0.1", 0), DeliverableHandler)
            port = self._server.server_address[1]
            self._base_url = f"http://127.0.0.1:{port}"
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._server_thread.start()
        except OSError:
            self._server = None
            self._base_url = f"http://127.0.0.1:{18900 + (id(self) % 1000)}"

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
        self._hosted_deliverables[int(job_id)] = new_content

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    def fulfill_job(self, job_id: int, task_desc: str) -> dict[str, Any]:
        """Verify job is Funded (when available), host deliverable via HTTP, and call submitResult."""
        if hasattr(self._cm, "get_job"):
            try:
                job = self._cm.get_job(job_id)
                if "state" in job and job["state"] != "Funded":
                    raise RuntimeError(
                        f"Provider {self._name} refuses job {job_id}: expected state Funded, got {job['state']}"
                    )
                if "provider" in job and Web3.to_checksum_address(job["provider"]) != self._address:
                    raise RuntimeError(
                        f"Provider {self._name} ({self._address}) is not assigned to job {job_id} ({job['provider']})"
                    )
            except KeyError:
                pass

        deliverable_text = self._generator(job_id, task_desc)
        self._hosted_deliverables[int(job_id)] = deliverable_text
        data_uri = f"{self._base_url}/deliverables/{int(job_id)}"
        result_hash: bytes = Web3.keccak(text=deliverable_text)

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
                deliverable_text=deliverable_text,
                provider_private_key=self._private_key,
                data_uri=data_uri,
            )

        return {
            "job_id": job_id,
            "provider": self._address,
            "deliverable": deliverable_text,
            "data_uri": data_uri,
            "result_hash": tx_res["result_hash"],
            "tx_hash": tx_res["tx_hash"],
        }

    def submit_for_job(self, job_id: int, task_desc: str) -> dict[str, Any]:
        """Alias for fulfill_job used by HTTP dataUri handshake tests."""
        return self.fulfill_job(job_id=job_id, task_desc=task_desc)
