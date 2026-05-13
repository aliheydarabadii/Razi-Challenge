"""Package-level logging entry point.

All modules obtain loggers from here so there is a single place to
change if the underlying logging library or configuration ever changes.

The pipeline itself is configured by bootstrap.logging.configure_logging().
"""

from __future__ import annotations

import structlog

get_logger = structlog.get_logger
