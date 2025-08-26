"""Minimal JSON logging with per-request trace_id.

Requirements satisfied: JSON-formatted logs and a ContextVar-held trace_id
that is injected into every log record via a logging.Filter. This file is
kept intentionally small for v0.0.
"""

import json
import logging
from contextvars import ContextVar

# ContextVar holding current trace id
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)


class TraceIdFilter(logging.Filter):
    """Attach trace_id from ContextVar to each LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_ctx.get(None)
        return True


class JsonFormatter(logging.Formatter):
    """Very small JSON formatter."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, "trace_id", None),
        }
        return json.dumps(obj, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Set root logger to use compact JSON formatter and attach TraceIdFilter."""
    root = logging.getLogger()
    if getattr(root, "pixie_configured", False):
        return

    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceIdFilter())
    root.handlers = [handler]

    # attach filter to uvicorn.access so requests logged by uvicorn include trace_id
    logging.getLogger("uvicorn.access").addFilter(TraceIdFilter())

    setattr(root, "pixie_configured", True)
