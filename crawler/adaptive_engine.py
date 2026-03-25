from __future__ import annotations

import re
from typing import Literal, Optional

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)

RenderingMode = Literal["js", "static"]

# SPA framework fingerprints that indicate JS rendering is required
_SPA_PATTERNS = [
    r'id=["\']root["\']',
    r'id=["\']app["\']',
    r'ng-version=["\']',
    r'data-reactroot',
    r'data-ng-app',
    r'x-ng-app',
    r'<script[^>]+type=["\']module["\']',
    r'__NEXT_DATA__',
    r'__NUXT__',
    r'window\.__INITIAL_STATE__',
    r'window\.angular',
    r'window\.React',
    r'data-server-rendered=["\']false["\']',
    r'v-cloak',
]

_SPA_RE = re.compile("|".join(_SPA_PATTERNS), re.IGNORECASE)

# Tags that represent content (vs markup/script)
_CONTENT_TAGS = re.compile(r"<(p|h[1-6]|li|td|th|article|section|main)\b", re.IGNORECASE)
_ALL_TAGS = re.compile(r"<[^>]+>")


def _text_ratio(html: str) -> float:
    """Return the ratio of visible text bytes to total HTML bytes (rough estimate)."""
    if not html:
        return 0.0
    text_stripped = _ALL_TAGS.sub("", html)
    text_len = len(text_stripped.strip())
    return text_len / len(html)


def _has_spa_fingerprint(html: str) -> bool:
    return bool(_SPA_RE.search(html))


def _has_meaningful_content(html: str, min_bytes: int = 3000, min_ratio: float = 0.25) -> bool:
    """Return True if the HTML response already contains enough readable text."""
    if len(html) < min_bytes:
        return False
    return _text_ratio(html) >= min_ratio


async def decide(
    url: str,
    force_js: bool = False,
    force_static: bool = False,
    adaptive: bool = True,
    user_agent: str = "Mozilla/5.0",
    extra_headers: Optional[dict] = None,
) -> RenderingMode:
    """
    Decide whether *url* requires JavaScript rendering or can be fetched statically.

    Decision tree:
    1. force_static / force_js config → immediate short-circuit
    2. adaptive=False → default to "js" (safe)
    3. Fetch HTML via httpx (timeout 8s)
    4. Inspect body for SPA fingerprints → "js"
    5. Text ratio < 0.15 → "js"
    6. Meaningful content present → "static"
    7. Fallback → "static"
    """
    if force_static:
        return "static"
    if force_js:
        return "js"
    if not adaptive:
        return "js"

    headers = {"User-Agent": user_agent}
    if extra_headers:
        headers.update(extra_headers)

    html = ""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code < 400:
                html = resp.text
    except Exception as exc:
        logger.debug("adaptive_engine: fetch failed for %s (%s), defaulting to js", url, exc)
        return "js"

    if not html:
        logger.debug("adaptive_engine: empty response for %s, defaulting to js", url)
        return "js"

    if _has_spa_fingerprint(html):
        logger.debug("adaptive_engine: SPA fingerprint detected → js (%s)", url)
        return "js"

    ratio = _text_ratio(html)
    if ratio < 0.15:
        logger.debug("adaptive_engine: low text ratio %.2f → js (%s)", ratio, url)
        return "js"

    if _has_meaningful_content(html):
        logger.debug("adaptive_engine: meaningful content present → static (%s)", url)
        return "static"

    logger.debug("adaptive_engine: fallback → static (%s)", url)
    return "static"
