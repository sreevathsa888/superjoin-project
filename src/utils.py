"""Small utilities for JSON, text, and logging behavior."""
from __future__ import annotations

import json
import logging
import re
from typing import Any


def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return logging.getLogger("fact_layer")


logger = setup_logging()


def json_loads_lenient(raw: str) -> Any:
    """Parse an LLM response, tolerating a Markdown code fence."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    return json.loads(cleaned)


def compact_text(value: str, limit: int = 160) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else f"{value[:limit - 1]}…"
