"""Minimal JSON logging with per-request trace_id.

Requirements satisfied: JSON-formatted logs and a ContextVar-held trace_id
that is injected into every log record via a logging.Filter. This file is
kept intentionally small for v0.0.
"""

import json
import logging
from contextvars import ContextVar
from typing import Optional

# Use Optional[str] for compatibility with Python versions that may not
# support the `str | None` syntax at runtime in some typing contexts.
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


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
        # include extra fields attached to LogRecord via `extra`
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

        noisy_fields = {"taskName", "task", "task_name"}

        for k, v in record.__dict__.items():
            # skip standard attrs, private attrs and noisy fields
            if k in standard_attrs or k.startswith("_") or k in noisy_fields:
                continue
            # skip empty / None values
            if v is None or (isinstance(v, str) and v == ""):
                continue
            # skip fields we already added
            if k in obj:
                continue
            try:
                json.dumps(v)
                obj[k] = v
            except Exception:
                # fallback to string representation for non-serializable values
                obj[k] = str(v)

        return json.dumps(obj, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Set root logger to use compact JSON formatter and attach TraceIdFilter."""
    root = logging.getLogger()
    if getattr(root, "pixie_configured", False):
        return

    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    # Ensure trace_id is attached at logger level so test capture handlers
    # (pytest caplog) and any other handlers see the attribute on the LogRecord.
    trace_filter = TraceIdFilter()
    handler.addFilter(trace_filter)
    root.addFilter(trace_filter)
    root.handlers = [handler]

    logging.getLogger("uvicorn.access").addFilter(TraceIdFilter())

    # Wrap the LogRecord factory so every new LogRecord contains a trace_id
    # attribute at creation time. This ensures test capture (caplog) and
    # third-party handlers receive records with the attribute already set.
    orig_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        rec = orig_factory(*args, **kwargs)
        try:
            rec.trace_id = trace_id_ctx.get(None)
        except Exception:
            rec.trace_id = None
        return rec

    logging.setLogRecordFactory(record_factory)

    setattr(root, "pixie_configured", True)
