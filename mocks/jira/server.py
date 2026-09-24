"""Native Python HTTP server for Mock Jira Cloud REST v3.

Provides deterministic responses for:
- Scenario A: PAY-117 (Transfer status delays, callback timeouts on partner switch)
- Scenario B: CORE-82 (KYC camera ratio bug, minor <2% impact)
- Scenario C: Wallet funding (Zero active Jira issues)
- Scenario D: PAY-134 (Bill payment DISCO vendor 502 Bad Gateway)
- Background / Noise tasks (CORE-101, PAY-95, PAY-110)
"""

import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from mocks.jira.expectations import get_jira_mock_expectations

logger = logging.getLogger(__name__)


class PocketJiraCompatHandler(BaseHTTPRequestHandler):
    """HTTP Request handler serving Jira Cloud REST v3 mock endpoints."""

    _expectations: list[dict[str, Any]] | None = None

    @classmethod
    def get_expectations(cls) -> list[dict[str, Any]]:
        if cls._expectations is None:
            cls._expectations = get_jira_mock_expectations()
        return cls._expectations

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard request logging in development
        pass

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        expectations = self.get_expectations()

        for exp in expectations:
            req = exp.get("httpRequest", {})
            if req.get("method") == "GET" and req.get("path") == path:
                resp = exp.get("httpResponse", {})
                status_code = resp.get("statusCode", 200)
                body = resp.get("body", {})

                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
                return

        # Not found
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "errorMessages": [f"Issue Does Not Exist or path '{path}' not found"],
                    "errors": {},
                }
            ).encode("utf-8")
        )

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

        try:
            payload = json.loads(post_body)
        except Exception:
            payload = {}

        expectations = self.get_expectations()

        if path == "/rest/api/3/search/jql":
            jql = (payload.get("jql") or "").upper()
            issue_by_key: dict[str, dict[str, Any]] = {}
            for exp in expectations:
                request_path = exp.get("httpRequest", {}).get("path", "")
                if request_path.startswith("/rest/api/3/issue/") and not request_path.endswith(
                    "/comment"
                ):
                    issue = exp.get("httpResponse", {}).get("body", {})
                    if issue.get("key"):
                        issue_by_key[issue["key"]] = issue

            if any(term in jql for term in ("WALLET", "FUNDING", "DEBIT CARD", "3DS")):
                keys: list[str] = []
            elif any(term in jql for term in ("IDENTITY", "DOCUMENT", "OCR", "CAMERA", "KYC")):
                keys = ["CORE-82"]
            elif any(
                term in jql
                for term in (
                    "ELECTRICITY",
                    "UTILITY",
                    "DISCO",
                    "BILL",
                    "TOKEN",
                    "MONTH-END",
                    "MONTH END",
                    "SETTLEMENT",
                    "PAYMENT TIMEOUT",
                )
            ):
                keys = ["PAY-134"]
            elif any(term in jql for term in ("TRANSFER", "CALLBACK", "WEBHOOK", "SWITCH", "BANK")):
                keys = ["PAY-117"]
            else:
                keys = []
            issues = [issue_by_key[key] for key in keys if key in issue_by_key]

            res = {
                "issues": issues,
                "nextPageToken": None,
                "isLast": True,
                "total": len(issues),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # Check other POST expectations
        for exp in expectations:
            req = exp.get("httpRequest", {})
            if req.get("method") == "POST" and req.get("path") == path:
                resp = exp.get("httpResponse", {})
                status_code = resp.get("statusCode", 200)
                body = resp.get("body", {})

                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
                return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"errorMessages": [f"Endpoint '{path}' not found"], "errors": {}}).encode(
                "utf-8"
            )
        )


class MockJiraServer:
    """Manages the background execution of the Mock Jira server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 1080) -> None:
        self.host = host
        self.port = port
        self.httpd: HTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the Mock Jira HTTP server in a background daemon thread."""
        self.httpd = HTTPServer((self.host, self.port), PocketJiraCompatHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Shutdown and terminate the Mock Jira HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None


def main() -> None:
    """Direct entrypoint for running the Mock Jira server."""
    port = int(os.getenv("MOCK_JIRA_PORT", "1080"))
    host = os.getenv("MOCK_JIRA_HOST", "0.0.0.0")
    print(f"Starting Pocket Mock Jira server on {host}:{port}...")
    server = HTTPServer((host, port), PocketJiraCompatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Mock Jira server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
