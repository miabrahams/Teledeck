from __future__ import annotations

import argparse
import logging

from app.container import get_container
from app.utils import load_image_from_source

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute the aesthetic score for an image using the Teledeck model stack.")
    parser.add_argument("image", help="Path or HTTP(S) URL to an image")
    parser.add_argument("--log-level", default="INFO", help="Python logging level (default: INFO)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    container = get_container()
    image = load_image_from_source(args.image, timeout=container.settings.request_timeout_seconds)
    result = container.aesthetic.score(image)
    LOGGER.info("Score: %.4f (backend=%s)", result.score, result.backend)


if __name__ == "__main__":
    main()
