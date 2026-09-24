"""Native Python server runner and lifecycle manager for Mock Zendesk."""

import os
import threading
from http.server import HTTPServer

from mocks.zendesk.compat_handler import PocketZendeskCompatHandler


class MockZendeskServer:
    """Manages the background execution of the Mock Zendesk server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.httpd: HTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the Mock Zendesk HTTP server in a background daemon thread."""
        self.httpd = HTTPServer((self.host, self.port), PocketZendeskCompatHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Shutdown and terminate the Mock Zendesk HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None


def main() -> None:
    """Direct entrypoint for running the Mock Zendesk server."""
    port = int(os.getenv("MOCK_ZENDESK_PORT", "8080"))
    host = os.getenv("MOCK_ZENDESK_HOST", "0.0.0.0")
    print(f"Starting Pocket Mock Zendesk server on {host}:{port}...")
    server = HTTPServer((host, port), PocketZendeskCompatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Mock Zendesk server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
