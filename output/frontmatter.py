from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml

from crawler.trafilatura_runner import ExtractionResult


def build(result: ExtractionResult, extra_fields: Optional[Dict[str, Any]] = None) -> str:
    """Return a YAML frontmatter block (including the --- delimiters) for *result*."""
    data: Dict[str, Any] = {
        "url": result.url,
        "title": result.title or "",
        "date_crawled": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_domain": _extract_domain(result.url),
        "depth": result.depth,
        "parent_url": result.parent_url or "",
        "word_count": len(result.raw_markdown.split()),
        "rendering_mode": result.rendering_mode,
    }

    if extra_fields:
        data.update(extra_fields)

    yaml_str = yaml.dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()

    return f"---\n{yaml_str}\n---\n"


def _extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc.lower()

