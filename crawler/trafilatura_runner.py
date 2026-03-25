from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import httpx
import trafilatura
from trafilatura.settings import use_config as trafilatura_use_config

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    """Unified extraction result returned by both runners."""
    url: str
    title: str
    raw_markdown: str
    links: List[str]
    status_code: int
    rendering_mode: str  # "js" or "static"
    error: Optional[str] = None
    # Populated by orchestrator
    depth: int = 0
    parent_url: str = ""


# Configure trafilatura to be more permissive
_traf_config = trafilatura_use_config()
_traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


async def run(
    url: str,
    user_agent: str,
    extra_headers: Optional[dict] = None,
    css_selector: Optional[str] = None,
    include_links: bool = True,
    include_images: bool = False,
    favor_recall: bool = True,
) -> ExtractionResult:
    """Fetch *url* with httpx and extract content via Trafilatura."""
    headers = {"User-Agent": user_agent}
    if extra_headers:
        headers.update(extra_headers)

    html: Optional[str] = None
    status_code = 0

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            status_code = resp.status_code
            html = resp.text
    except httpx.RequestError as exc:
        logger.warning("HTTP error fetching %s: %s", url, exc)
        return ExtractionResult(
            url=url, title="", raw_markdown="", links=[], status_code=0,
            rendering_mode="static", error=str(exc),
        )

    if not html or status_code >= 400:
        return ExtractionResult(
            url=url, title="", raw_markdown="", links=[],
            status_code=status_code, rendering_mode="static",
            error=f"HTTP {status_code}",
        )

    # Extract main content as Markdown
    markdown = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_links=include_links,
        include_images=include_images,
        favor_recall=favor_recall,
        config=_traf_config,
        target_language=None,
    ) or ""

    # Extract metadata for title
    meta = trafilatura.extract_metadata(html, default_url=url)
    title = ""
    if meta:
        title = meta.title or meta.sitename or ""

    # Extract internal links for BFS frontier
    links = _extract_links(html, base_url=url) if include_links else []

    return ExtractionResult(
        url=url,
        title=title,
        raw_markdown=markdown,
        links=links,
        status_code=status_code,
        rendering_mode="static",
    )


def _extract_links(html: str, base_url: str) -> List[str]:
    """Extract absolute href links from raw HTML using trafilatura's internal utilities."""
    from trafilatura.utils import load_html
    from lxml.html import iterlinks

    try:
        tree = load_html(html)
        if tree is None:
            return []
        links = []
        for _, _, href, _ in iterlinks(tree):
            if href and href.startswith("http"):
                links.append(href)
            elif href and not href.startswith(("#", "mailto:", "javascript:")):
                from urllib.parse import urljoin
                links.append(urljoin(base_url, href))
        return list(dict.fromkeys(links))  # deduplicate, preserve order
    except Exception:
        return []
