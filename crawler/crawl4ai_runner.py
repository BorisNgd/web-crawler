from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from utils.logger import get_logger
from crawler.trafilatura_runner import ExtractionResult

if TYPE_CHECKING:
    from crawl4ai import AsyncWebCrawler
    from utils.config_loader import CrawlerConfig

logger = get_logger(__name__)


def _build_browser_config(config: "CrawlerConfig", extra_cookies: Optional[list] = None):
    """Build a Crawl4AI BrowserConfig from CrawlerConfig."""
    from crawl4ai import BrowserConfig

    cookies = []
    # Cookie auth
    if config.auth.type == "cookie":
        for c in config.auth.cookies:
            cookies.append({
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
            })
    # Cookies exported by form auth
    if extra_cookies:
        cookies.extend(extra_cookies)

    # Header auth
    headers = {}
    if config.auth.type == "header":
        headers.update(config.auth.headers)

    return BrowserConfig(
        headless=True,
        browser_type="chromium",
        user_agent=config.user_agent,
        headers=headers if headers else None,
        cookies=cookies if cookies else None,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
    )


def _build_run_config(config: "CrawlerConfig", url: str):
    """Build a Crawl4AI CrawlerRunConfig for a single URL."""
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

    # Content filter selection
    content_filter = None
    if config.extraction.content_filter == "bm25":
        from crawl4ai.content_filter_strategy import BM25ContentFilter
        content_filter = BM25ContentFilter(
            bm25_threshold=config.extraction.bm25_threshold
        )
    elif config.extraction.content_filter == "pruning":
        from crawl4ai.content_filter_strategy import PruningContentFilter
        content_filter = PruningContentFilter(threshold=0.45)

    # content_filter belongs to DefaultMarkdownGenerator, not CrawlerRunConfig
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={
            "ignore_links": not config.extraction.include_links,
            "ignore_images": not config.extraction.include_images,
        },
    )

    excluded = ",".join(config.extraction.exclude_selectors) if config.extraction.exclude_selectors else None

    # JS snippet for scroll behavior
    js_code = config.custom_js_snippet
    if not js_code and config.js_scroll_behavior == "auto":
        # Must NOT use top-level await — wrap in IIFE for compatibility
        js_code = (
            "(function(){"
            "window.scrollTo(0, document.body.scrollHeight);"
            "})();"
        )

    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for=config.wait_for_selector,
        js_code=js_code,
        word_count_threshold=10,
        markdown_generator=md_generator,
        css_selector=config.extraction.css_selector,
        excluded_selector=excluded,
        page_timeout=config.js_timeout,
        scan_full_page=True,
        verbose=False,
    )


async def run(
    url: str,
    crawler: "AsyncWebCrawler",
    config: "CrawlerConfig",
) -> ExtractionResult:
    """Run Crawl4AI on *url* using the shared *crawler* instance."""
    run_cfg = _build_run_config(config, url)

    try:
        result = await crawler.arun(url=url, config=run_cfg)
    except Exception as exc:
        logger.warning("Crawl4AI error on %s: %s", url, exc)
        return ExtractionResult(
            url=url, title="", raw_markdown="", links=[],
            status_code=0, rendering_mode="js", error=str(exc),
        )

    if not result.success:
        logger.warning("Crawl4AI failed for %s: %s", url, result.error_message)
        return ExtractionResult(
            url=url, title="", raw_markdown="", links=[],
            status_code=result.status_code or 0,
            rendering_mode="js",
            error=result.error_message,
        )

    # Prefer BM25-filtered markdown when available
    md_obj = result.markdown
    markdown = ""
    if md_obj:
        markdown = (md_obj.fit_markdown or md_obj.raw_markdown or "").strip()

    title = ""
    if result.metadata:
        title = result.metadata.get("title") or result.metadata.get("og:title") or ""

    # Collect internal + external links for BFS
    links: List[str] = []
    if result.links:
        for link_info in result.links.get("internal", []):
            href = link_info.get("href") if isinstance(link_info, dict) else str(link_info)
            if href:
                links.append(href)
        for link_info in result.links.get("external", []):
            href = link_info.get("href") if isinstance(link_info, dict) else str(link_info)
            if href:
                links.append(href)

    return ExtractionResult(
        url=url,
        title=title,
        raw_markdown=markdown,
        links=list(dict.fromkeys(links)),
        status_code=result.status_code or 200,
        rendering_mode="js",
    )
