from __future__ import annotations

import asyncio
import contextlib
import logging

import uvicorn

from .container import get_container
from .grpc_server import create_grpc_server
from .http_api import create_http_app

LOGGER = logging.getLogger(__name__)


async def serve() -> None:
    container = get_container()

    tasks: list[asyncio.Task[None]] = []
    stop_event = asyncio.Event()

    grpc_server = None

    if container.settings.enable_http:
        http_app = create_http_app(container)
        http_config = uvicorn.Config(
            http_app,
            host=container.settings.http_host,
            port=container.settings.http_port,
            log_level=container.settings.log_level,
            loop="asyncio",
        )
        http_server = uvicorn.Server(http_config)

        async def _run_http() -> None:
            try:
                await http_server.serve()
            finally:
                stop_event.set()

        tasks.append(asyncio.create_task(_run_http()))
    else:
        LOGGER.warning("HTTP server disabled via ENABLE_HTTP=0")

    if container.settings.enable_grpc:
        grpc_server = await create_grpc_server(container)
        await grpc_server.start()

        async def _run_grpc() -> None:
            try:
                await grpc_server.wait_for_termination()
            finally:
                stop_event.set()

        tasks.append(asyncio.create_task(_run_grpc()))
    else:
        LOGGER.warning("gRPC server disabled via ENABLE_GRPC=0")

    if not tasks:
        raise RuntimeError("Both HTTP and gRPC servers are disabled. Enable at least one entry point.")

    await stop_event.wait()

    for task in tasks:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    if grpc_server is not None:
        await grpc_server.stop(grace=5)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested by user")


__all__ = ["main", "serve"]
