from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from utils.config_loader import CookieConfig


def to_playwright_cookies(cookie_configs: List["CookieConfig"]) -> List[dict]:
    """Convert CookieConfig objects to the Playwright/Crawl4AI cookie dict format."""
    return [
        {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path,
            "secure": c.secure,
            "httpOnly": c.http_only,
        }
        for c in cookie_configs
    ]
