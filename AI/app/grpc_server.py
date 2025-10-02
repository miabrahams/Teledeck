from __future__ import annotations

import asyncio
import logging
from typing import Any

import grpc
from grpc import aio

from .container import ServiceContainer, get_container
from ..proto import ai_server_pb2, ai_server_pb2_grpc
from .utils import ImageSourceError, load_image_from_source

LOGGER = logging.getLogger(__name__)


class ImageScorerService(ai_server_pb2_grpc.ImageScorerServicer):
    def __init__(self, container: ServiceContainer) -> None:
        self._container = container

    async def PredictUrl(self, request: ai_server_pb2.ImageUrlRequest, context: aio.ServicerContext) -> ai_server_pb2.ScoreResult:
        try:
            image = await asyncio.to_thread(
                load_image_from_source,
                request.image_url,
                timeout=self._container.settings.request_timeout_seconds,
            )
        except ImageSourceError as exc:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return ai_server_pb2.ScoreResult()
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Unexpected error while loading image")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return ai_server_pb2.ScoreResult()

        try:
            result = await asyncio.to_thread(self._container.aesthetic.score, image)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Aesthetic scoring failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Aesthetic scoring failed")
            return ai_server_pb2.ScoreResult()

        return ai_server_pb2.ScoreResult(score=result.score)

    async def TagUrl(self, request: ai_server_pb2.TagImageUrlRequest, context: aio.ServicerContext) -> ai_server_pb2.TagResult:
        try:
            image = await asyncio.to_thread(
                load_image_from_source,
                request.image_url,
                timeout=self._container.settings.request_timeout_seconds,
            )
        except ImageSourceError as exc:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return ai_server_pb2.TagResult()
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Unexpected error while loading image")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return ai_server_pb2.TagResult()

        try:
            predictions = await asyncio.to_thread(self._container.tagger.predict, image, request.cutoff if request.cutoff else None)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Tagging failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Tagging failed")
            return ai_server_pb2.TagResult()

        tags = [ai_server_pb2.Tag(weight=item.weight, tag=item.tag) for item in predictions]
        return ai_server_pb2.TagResult(tags=tags)


async def create_grpc_server(container: ServiceContainer | None = None) -> aio.Server:
    if container is None:
        container = get_container()

    server = aio.server()
    ai_server_pb2_grpc.add_ImageScorerServicer_to_server(ImageScorerService(container), server)
    listen_addr = f"[::]:{container.settings.grpc_port}"
    server.add_insecure_port(listen_addr)
    LOGGER.info("gRPC server listening on %s", listen_addr)
    return server


__all__ = ["create_grpc_server"]
