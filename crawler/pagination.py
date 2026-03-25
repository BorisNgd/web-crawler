from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, List, Optional, Tuple
from urllib.parse import urljoin

import httpx

from utils.logger import get_logger

if TYPE_CHECKING:
    from crawl4ai import AsyncWebCrawler
    from utils.config_loader import CrawlerConfig, PaginationConfig

logger = get_logger(__name__)


async def get_paginated_urls(
    url: str,
    html_or_markdown: str,
    config: "CrawlerConfig",
    crawler: Optional["AsyncWebCrawler"] = None,
) -> Tuple[List[str], str]:
    """
    Detect and handle pagination for *url*.

    Returns:
        - extra_urls: additional page URLs to enqueue (URL-pattern mode)
        - extra_markdown: additional markdown content to merge (scroll/load-more mode)
    """
    pg = config.pagination
    if not pg.enabled:
        return [], ""

    mode = pg.mode
    if mode == "auto":
        mode = await _detect_mode(url, html_or_markdown, config)

    logger.debug("pagination mode=%s for %s", mode, url)

    if mode == "url_pattern":
        return await _url_pattern(url, pg), ""

    if mode == "scroll" and crawler is not None:
        extra_md = await _infinite_scroll(url, pg, crawler, config)
        return [], extra_md

    if mode == "load_more" and crawler is not None:
        extra_md = await _load_more(url, pg, crawler, config)
        return [], extra_md

    return [], ""


async def _detect_mode(url: str, content: str, config: "CrawlerConfig") -> str:
    """Heuristic auto-detection of pagination mode from page content."""
    pg = config.pagination

    # URL pattern: look for <a rel="next"> or common "next page" links
    if re.search(r'rel=["\']next["\']', content, re.IGNORECASE):
        return "url_pattern"

    # Configured load-more selector
    if pg.load_more_selector and re.search(
        re.escape(pg.load_more_selector), content, re.IGNORECASE
    ):
        return "load_more"

    # Common "load more" button patterns
    if re.search(
        r'(load[- ]more|voir plus|afficher plus|show more|charger plus)',
        content, re.IGNORECASE
    ):
        return "load_more"

    # Infinite scroll indicators
    if re.search(
        r'(infinite[- ]scroll|data-infinite|IntersectionObserver)',
        content, re.IGNORECASE
    ):
        return "scroll"

    return "none"


async def _url_pattern(url: str, pg: "PaginationConfig") -> List[str]:
    """Generate additional page URLs using explicit pattern or rel=next links."""
    urls = []

    # Explicit pattern configured (e.g. "?page={n}" or "/page/{n}/")
    if pg.url_pattern:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            for page_num in range(2, pg.max_pages + 1):
                if "{n}" in pg.url_pattern:
                    candidate = urljoin(url, pg.url_pattern.replace("{n}", str(page_num)))
                else:
                    break
                try:
                    resp = await client.head(candidate, timeout=5.0)
                    if resp.status_code < 400:
                        urls.append(candidate)
                    else:
                        break  # Stop at first missing page
                except Exception:
                    break
        return urls

    # Auto-generate common patterns from the original URL
    for pattern in [
        "?page={n}", "&page={n}", "/page/{n}/", "?p={n}", "/p/{n}/",
    ]:
        candidate = urljoin(url, pattern.replace("{n}", "2"))
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.head(candidate)
                if resp.status_code < 400:
                    # Pattern works — generate full range
                    for n in range(2, pg.max_pages + 1):
                        page_url = urljoin(url, pattern.replace("{n}", str(n)))
                        async with httpx.AsyncClient(timeout=5.0) as c:
                            r = await c.head(page_url)
                            if r.status_code < 400:
                                urls.append(page_url)
                            else:
                                break
                    return urls
        except Exception:
            continue

    return urls


async def _infinite_scroll(
    url: str,
    pg: "PaginationConfig",
    crawler: "AsyncWebCrawler",
    config: "CrawlerConfig",
) -> str:
    """Scroll the page incrementally and collect all Markdown content."""
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

    collected_parts: List[str] = []
    prev_height = 0

    for i in range(pg.max_pages):
        scroll_js = f"""
window.scrollTo(0, document.body.scrollHeight);
await new Promise(r => setTimeout(r, {int(pg.scroll_pause * 1000)}));
"""
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=scroll_js,
            scan_full_page=True,
            markdown_generator=DefaultMarkdownGenerator(
                options={"ignore_links": not config.extraction.include_links}
            ),
            page_timeout=config.js_timeout,
            verbose=False,
        )
        try:
            result = await crawler.arun(url=url, config=run_cfg)
        except Exception as exc:
            logger.warning("scroll pagination error on page %d: %s", i + 1, exc)
            break

        if not result.success:
            break

        md = ""
        if result.markdown:
            md = (result.markdown.raw_markdown or "").strip()

        if md and md not in collected_parts:
            collected_parts.append(md)

        # Detect stall: check if page height changed
        height_js_result = None
        try:
            height_js_result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    js_code="return document.body.scrollHeight;",
                    cache_mode=CacheMode.BYPASS,
                    verbose=False,
                ),
            )
        except Exception:
            pass

        new_height = prev_height  # fallback: can't determine → assume stalled after 2 retries
        if height_js_result and height_js_result.success and height_js_result.markdown:
            try:
                new_height = int(height_js_result.markdown.raw_markdown.strip())
            except ValueError:
                pass

        if new_height == prev_height:
            logger.debug("scroll: page height unchanged at iteration %d, stopping", i + 1)
            break
        prev_height = new_height
        await asyncio.sleep(pg.scroll_pause)

    # Return the last (most complete) collected markdown
    return collected_parts[-1] if collected_parts else ""


async def _load_more(
    url: str,
    pg: "PaginationConfig",
    crawler: "AsyncWebCrawler",
    config: "CrawlerConfig",
) -> str:
    """Click a 'load more' button repeatedly and return the final full-page Markdown."""
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

    selector = pg.load_more_selector or "button:has-text('load more'), button:has-text('voir plus')"

    click_js = f"""
const btn = document.querySelector('{selector}');
if (btn) {{ btn.click(); }}
await new Promise(r => setTimeout(r, {int(pg.scroll_pause * 1000)}));
"""
    last_markdown = ""
    prev_word_count = 0

    for i in range(pg.max_pages):
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=click_js,
            scan_full_page=True,
            markdown_generator=DefaultMarkdownGenerator(
                options={"ignore_links": not config.extraction.include_links}
            ),
            page_timeout=config.js_timeout,
            verbose=False,
        )
        try:
            result = await crawler.arun(url=url, config=run_cfg)
        except Exception as exc:
            logger.warning("load_more pagination error on click %d: %s", i + 1, exc)
            break

        if not result.success:
            break

        md = ""
        if result.markdown:
            md = (result.markdown.raw_markdown or "").strip()

        word_count = len(md.split())
        if word_count <= prev_word_count:
            logger.debug("load_more: no new content at click %d, stopping", i + 1)
            break

        last_markdown = md
        prev_word_count = word_count
        await asyncio.sleep(pg.scroll_pause)

    return last_markdown
