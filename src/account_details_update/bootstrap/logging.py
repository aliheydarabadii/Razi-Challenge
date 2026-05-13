"""Application logging configuration."""

from __future__ import annotations

import logging
import sys

import structlog

get_logger = structlog.get_logger


def configure_logging() -> None:
    """Configure structured JSON logging for the application.

    All log output — including third-party libraries such as httpx and
    tenacity — is emitted as newline-delimited JSON to stdout.

    Example output:
        {"level": "info", "logger": "httpx", "timestamp": "2026-05-12T17:29:16Z",
         "event": "HTTP Request: POST https://..."}
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure structlog for any code that uses structlog directly.
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Bridge stdlib logging (httpx, tenacity, etc.) through the same chain.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
