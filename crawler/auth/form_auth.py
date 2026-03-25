from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from utils.logger import get_logger

if TYPE_CHECKING:
    from utils.config_loader import AuthConfig

logger = get_logger(__name__)


async def login_and_get_cookies(auth: "AuthConfig", user_agent: str) -> Optional[List[dict]]:
    """
    Perform a form-based login using Playwright and return the session cookies
    in the Crawl4AI/Playwright cookie dict format.

    Returns None if login could not be completed.
    """
    if not auth.login_url or not auth.username or not auth.password:
        logger.error("form_auth: login_url, username, and password are required")
        return None

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("form_auth: playwright is not installed")
        return None

    cookies: Optional[List[dict]] = None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        try:
            logger.info("form_auth: navigating to login page %s", auth.login_url)
            await page.goto(auth.login_url, wait_until="networkidle", timeout=30_000)

            await page.fill(auth.username_selector, auth.username)
            await page.fill(auth.password_selector, auth.password)
            await page.click(auth.submit_selector)

            # Wait for evidence of successful login
            if auth.success_selector:
                await page.wait_for_selector(auth.success_selector, timeout=15_000)
                logger.info("form_auth: login succeeded (found success_selector)")
            else:
                await page.wait_for_load_state("networkidle", timeout=15_000)
                logger.info("form_auth: login completed (no success_selector configured)")

            raw_cookies = await context.cookies()
            cookies = [
                {
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c.get("domain", ""),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", False),
                    "httpOnly": c.get("httpOnly", False),
                }
                for c in raw_cookies
            ]
            logger.info("form_auth: exported %d cookies", len(cookies))

        except Exception as exc:
            logger.error("form_auth: login failed — %s", exc)
            cookies = None
        finally:
            await browser.close()

    return cookies
