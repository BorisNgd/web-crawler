from __future__ import annotations

from dataclasses import dataclass
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


def _html2text_convert(html_fragment: str, include_links: bool = True) -> str:
    """Convert HTML to Markdown using html2text — tolerant of page builder structures."""
    try:
        import html2text as h2t
        converter = h2t.HTML2Text()
        converter.ignore_links = not include_links
        converter.ignore_images = True
        converter.body_width = 0          # no line wrapping
        converter.unicode_snob = True
        converter.skip_internal_links = True
        result = converter.handle(html_fragment).strip()
        # Remove excessive blank lines introduced by nested divs
        import re
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result
    except ImportError:
        logger.debug("html2text not available, skipping fallback")
        return ""
    except Exception as exc:
        logger.debug("html2text conversion failed: %s", exc)
        return ""


def _narrow_html(html: str, css_selector: str) -> str:
    """Return the outer HTML of the first element matching *css_selector*, or full html on failure."""
    try:
        from trafilatura.utils import load_html
        from lxml import etree

        tree = load_html(html)
        if tree is None:
            return html

        elements = tree.cssselect(css_selector)
        if not elements:
            logger.debug("css_selector '%s' matched no elements", css_selector)
            return html

        elem = elements[0]
        fragment = etree.tostring(elem, encoding="unicode", method="html")
        # Wrap in a minimal HTML document so Trafilatura can parse it correctly
        narrowed = f"<html><head></head><body>{fragment}</body></html>"
        logger.debug("css_selector '%s' narrowed HTML from %d to %d chars",
                     css_selector, len(html), len(narrowed))
        return narrowed
    except Exception as exc:
        logger.debug("css_selector narrowing failed (%s), using full HTML", exc)
        return html


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

    if css_selector:
        # Narrow to the targeted element, then use html2text directly.
        # html2text is more permissive than Trafilatura on page builder structures
        # (Beaver Builder, Elementor, Divi) where content is in deeply nested divs.
        narrowed = _narrow_html(html, css_selector)
        if narrowed != html:
            markdown = _html2text_convert(narrowed, include_links=include_links)
            logger.debug("html2text extracted %d chars from narrowed HTML for %s",
                         len(markdown), url)
        else:
            markdown = ""
    else:
        markdown = ""

    # Fallback: Trafilatura on full HTML (no css_selector, or narrowing failed)
    if not markdown:
        logger.debug("Using Trafilatura on full HTML for %s", url)
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
