import json
import logging
from contextvars import ContextVar
from typing import Optional

trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        record.trace_id = trace_id_ctx.get(None)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, "trace_id", None),
        }
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            try:
                json.dumps(value)
            except Exception:
                value = str(value)
            payload.setdefault(key, value)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if getattr(root, "pixie_configured", False):
        return
    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    trace_filter = TraceIdFilter()
    handler.addFilter(trace_filter)
    root.addFilter(trace_filter)
    root.handlers = [handler]
    logging.getLogger("uvicorn.access").addFilter(trace_filter)
    factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = factory(*args, **kwargs)
        record.trace_id = trace_id_ctx.get(None)
        return record

    logging.setLogRecordFactory(record_factory)
    setattr(root, "pixie_configured", True)
