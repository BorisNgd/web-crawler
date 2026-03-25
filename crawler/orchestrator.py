from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from utils.config_loader import CrawlerConfig
from utils.logger import get_logger
from utils.url_utils import (
    is_in_scope,
    matches_any_pattern,
    normalize_url,
    resolve_url,
)
from crawler import robots as robots_module
from crawler import adaptive_engine
from crawler import crawl4ai_runner
from crawler import trafilatura_runner
from crawler.trafilatura_runner import ExtractionResult
from crawler import pagination as pagination_module
from output import writer

logger = get_logger(__name__)


@dataclass
class _QueueItem:
    url: str
    depth: int
    parent_url: str = ""


@dataclass
class CrawlStats:
    pages_crawled: int = 0
    pages_skipped: int = 0
    pages_failed: int = 0
    files_written: int = 0
    start_time: float = field(default_factory=time.time)

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def summary(self) -> str:
        return (
            f"Crawl complete in {self.elapsed():.1f}s — "
            f"{self.pages_crawled} crawled, "
            f"{self.pages_skipped} skipped, "
            f"{self.pages_failed} failed, "
            f"{self.files_written} files written."
        )


class Orchestrator:
    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self.stats = CrawlStats()
        self._visited: Set[str] = set()
        self._domain_last_access: Dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(config.concurrency)
        # Optional: extra cookies from form auth
        self._extra_cookies: Optional[List[dict]] = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(self) -> CrawlStats:
        logger.info("Starting crawl: %s (depth=%d, max_pages=%d)",
                    self.config.start_url, self.config.depth, self.config.max_pages)

        writer.reset_name_registry()

        # Pre-crawl authentication (form login → export cookies)
        await self._authenticate()

        # Build a single shared AsyncWebCrawler for all JS pages
        from crawl4ai import AsyncWebCrawler
        browser_cfg = crawl4ai_runner._build_browser_config(
            self.config, extra_cookies=self._extra_cookies
        )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            queue: asyncio.Queue[_QueueItem] = asyncio.Queue()
            queue.put_nowait(_QueueItem(
                url=self.config.start_url,
                depth=0,
                parent_url="",
            ))

            tasks: list[asyncio.Task] = []

            while not queue.empty() or any(not t.done() for t in tasks):
                # Clean up completed tasks
                tasks = [t for t in tasks if not t.done()]

                if self.stats.pages_crawled >= self.config.max_pages:
                    break

                if queue.empty():
                    if tasks:
                        await asyncio.sleep(0.1)
                    continue

                item = queue.get_nowait()
                norm_url = normalize_url(item.url)

                # --- Filtering ---
                if norm_url in self._visited:
                    self.stats.pages_skipped += 1
                    continue
                self._visited.add(norm_url)

                if not is_in_scope(item.url, self.config.start_url, self.config.url_filters.include_domains):
                    logger.debug("Out of scope: %s", item.url)
                    self.stats.pages_skipped += 1
                    continue

                if self.config.url_filters.exclude_patterns and matches_any_pattern(
                    item.url, self.config.url_filters.exclude_patterns
                ):
                    logger.debug("Excluded by pattern: %s", item.url)
                    self.stats.pages_skipped += 1
                    continue

                if self.config.url_filters.include_patterns and not matches_any_pattern(
                    item.url, self.config.url_filters.include_patterns
                ):
                    logger.debug("Not in include_patterns: %s", item.url)
                    self.stats.pages_skipped += 1
                    continue

                # Create crawl task
                task = asyncio.create_task(
                    self._crawl_one(item, crawler, queue)
                )
                tasks.append(task)

            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(self.stats.summary())
        return self.stats

    # ------------------------------------------------------------------
    # Single page crawl
    # ------------------------------------------------------------------

    async def _crawl_one(
        self,
        item: _QueueItem,
        crawler,
        queue: asyncio.Queue,
    ) -> None:
        url = item.url

        # robots.txt check
        if self.config.respect_robots_txt:
            allowed = await robots_module.can_fetch(url, self.config.user_agent)
            if not allowed:
                self.stats.pages_skipped += 1
                return

        async with self._semaphore:
            await self._polite_delay(url)

            try:
                result = await self._extract(url, crawler)
            except Exception as exc:
                logger.error("Unexpected error crawling %s: %s", url, exc)
                self.stats.pages_failed += 1
                return

        if result.error and not result.raw_markdown:
            logger.warning("Failed: %s — %s", url, result.error)
            self.stats.pages_failed += 1
            return

        result.depth = item.depth
        result.parent_url = item.parent_url

        # Handle pagination: merge scroll/load-more content, enqueue URL-pattern pages
        extra_urls, extra_markdown = await pagination_module.get_paginated_urls(
            url=url,
            html_or_markdown=result.raw_markdown,
            config=self.config,
            crawler=crawler if result.rendering_mode == "js" else None,
        )

        if extra_markdown:
            result.raw_markdown = extra_markdown  # replace with richer paginated content

        # Write output
        out_path = writer.write(result, self.config)
        if out_path:
            self.stats.files_written += 1

        self.stats.pages_crawled += 1
        logger.info("[%d/%d] %s → %s",
                    self.stats.pages_crawled, self.config.max_pages,
                    url, out_path or "(skipped empty)")

        # Enqueue discovered links (if depth allows)
        if item.depth < self.config.depth:
            # URL-pattern pagination pages
            for next_url in extra_urls:
                norm = normalize_url(next_url)
                if norm not in self._visited:
                    queue.put_nowait(_QueueItem(next_url, item.depth + 1, url))

            # Standard internal links
            for link_href in result.links:
                resolved = resolve_url(url, link_href)
                if not resolved:
                    continue
                norm = normalize_url(resolved)
                if norm not in self._visited:
                    queue.put_nowait(_QueueItem(resolved, item.depth + 1, url))

    # ------------------------------------------------------------------
    # Extraction dispatch
    # ------------------------------------------------------------------

    async def _extract(self, url: str, crawler) -> ExtractionResult:
        """Choose static or JS extraction based on adaptive engine."""
        mode = await adaptive_engine.decide(
            url=url,
            force_js=self.config.force_js,
            force_static=self.config.force_static,
            adaptive=self.config.adaptive_rendering,
            user_agent=self.config.user_agent,
            extra_headers=self.config.auth.headers if self.config.auth.type == "header" else None,
        )

        if mode == "static":
            extra_headers = {}
            if self.config.auth.type == "header":
                extra_headers = self.config.auth.headers
            result = await trafilatura_runner.run(
                url=url,
                user_agent=self.config.user_agent,
                extra_headers=extra_headers or None,
                css_selector=self.config.extraction.css_selector,
                include_links=self.config.extraction.include_links,
                include_images=self.config.extraction.include_images,
            )
        else:
            result = await crawl4ai_runner.run(url=url, crawler=crawler, config=self.config)
            # Fallback to Trafilatura if Crawl4AI returned empty content
            if not result.raw_markdown and not result.error:
                logger.debug("Crawl4AI empty result, falling back to Trafilatura for %s", url)
                result = await trafilatura_runner.run(
                    url=url,
                    user_agent=self.config.user_agent,
                    include_links=self.config.extraction.include_links,
                    include_images=self.config.extraction.include_images,
                )
                result.rendering_mode = "static"

        return result

    # ------------------------------------------------------------------
    # Politeness
    # ------------------------------------------------------------------

    async def _polite_delay(self, url: str) -> None:
        from utils.url_utils import extract_domain
        domain = extract_domain(url)
        last = self._domain_last_access.get(domain, 0.0)
        elapsed = time.monotonic() - last

        # Respect robots.txt crawl-delay if higher than configured delay
        delay = self.config.delay_between_requests
        if self.config.respect_robots_txt:
            robots_delay = await robots_module.get_crawl_delay(
                url, self.config.user_agent, default=delay
            )
            delay = max(delay, robots_delay)

        wait = delay - elapsed
        if wait > 0:
            await asyncio.sleep(wait)

        self._domain_last_access[domain] = time.monotonic()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def _authenticate(self) -> None:
        auth = self.config.auth

        if auth.type == "form":
            from crawler.auth.form_auth import login_and_get_cookies
            logger.info("Performing form-based login at %s", auth.login_url)
            self._extra_cookies = await login_and_get_cookies(auth, self.config.user_agent)
            if not self._extra_cookies:
                logger.warning("Form login returned no cookies — proceeding without auth")
        elif auth.type == "cookie":
            from crawler.auth.cookie_auth import to_playwright_cookies
            self._extra_cookies = to_playwright_cookies(auth.cookies)
            logger.info("Using %d configured cookies", len(self._extra_cookies))
        elif auth.type == "header":
            logger.info("Using header-based auth (%d headers)", len(auth.headers))
        # "none" → nothing to do
