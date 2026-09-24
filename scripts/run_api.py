"""Start the local API with an event loop compatible with Psycopg checkpoints."""

import asyncio
import selectors
import sys

import uvicorn


def main() -> None:
    config = uvicorn.Config("app.api.main:app", host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        with asyncio.Runner(
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        ) as runner:
            runner.run(server.serve())
        return
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
