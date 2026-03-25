from __future__ import annotations

import asyncio
import urllib.robotparser
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)

# In-process cache: domain → (RobotFileParser, crawl_delay)
_cache: Dict[str, tuple[urllib.robotparser.RobotFileParser, Optional[float]]] = {}
_cache_lock = asyncio.Lock()


async def _fetch_robots(domain: str, scheme: str, user_agent: str) -> tuple[urllib.robotparser.RobotFileParser, Optional[float]]:
    robots_url = f"{scheme}://{domain}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
            resp = await client.get(robots_url, headers={"User-Agent": user_agent})
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                # No robots.txt or inaccessible → allow everything
                rp.parse([])
    except Exception as exc:
        logger.debug("Could not fetch robots.txt for %s: %s", domain, exc)
        rp.parse([])

    crawl_delay: Optional[float] = rp.crawl_delay(user_agent) or rp.crawl_delay("*")
    return rp, crawl_delay


async def get_robots(url: str, user_agent: str) -> tuple[urllib.robotparser.RobotFileParser, Optional[float]]:
    """Return (RobotFileParser, crawl_delay) for the domain of *url*, using a cache."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    scheme = parsed.scheme.lower()
    key = f"{scheme}://{domain}"

    async with _cache_lock:
        if key not in _cache:
            _cache[key] = await _fetch_robots(domain, scheme, user_agent)

    return _cache[key]


async def can_fetch(url: str, user_agent: str) -> bool:
    """Return True if robots.txt permits fetching *url* with the given user agent."""
    rp, _ = await get_robots(url, user_agent)
    allowed = rp.can_fetch(user_agent, url) or rp.can_fetch("*", url)
    if not allowed:
        logger.info("[ROBOTS_BLOCKED] %s", url)
    return allowed


async def get_crawl_delay(url: str, user_agent: str, default: float = 1.0) -> float:
    """Return the crawl delay specified by robots.txt, or *default* if none."""
    _, delay = await get_robots(url, user_agent)
    return delay if delay is not None else default
