import logging, json, time
from fastapi import Request
from app.api.schemas import ClassificationResponse
from typing import Optional

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("app")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
    return logger

def log_classification(logger: logging.Logger, request: Request, source: str, input_bytes: int, res: ClassificationResponse, note: Optional[str] = None) -> None:
    logger.info(json.dumps({
        "ts": int(time.time()),
        "rid": getattr(request.state, "rid", None),
        "source": source,
        "input_bytes": input_bytes,
        "category": res.category,
        "subtype": res.subtype,
        "confidence": round(res.confidence, 3),
        "truncated": ("truncated" in " ".join(res.reasons).lower()),
        "note": note,
    }))