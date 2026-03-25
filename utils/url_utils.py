from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse, urlencode, parse_qsl


def normalize_url(url: str) -> str:
    """Return a canonical, comparable URL (lowercase scheme+host, sorted query, no fragment)."""
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Sort query string for canonical comparison
    sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
    # Rebuild
    normalized = urlunparse((scheme, netloc, parsed.path, parsed.params, sorted_query, ""))
    return normalized


def extract_domain(url: str) -> str:
    """Return the netloc (host[:port]) of the URL."""
    return urlparse(url).netloc.lower()


def is_same_domain(url: str, base_url: str) -> bool:
    """Return True if url shares the same domain (netloc) as base_url."""
    return extract_domain(url) == extract_domain(base_url)


def is_in_scope(url: str, start_url: str, include_domains: list[str]) -> bool:
    """
    Return True if url is allowed to be crawled.

    Scope rules (in order):
    1. If include_domains is non-empty, url must belong to one of those domains.
    2. Otherwise, url must share the same domain as start_url.
    """
    domain = extract_domain(url)
    if include_domains:
        return any(domain == d.lower() or domain.endswith("." + d.lower()) for d in include_domains)
    return is_same_domain(url, start_url)


def resolve_url(base: str, href: str) -> Optional[str]:
    """Resolve a possibly relative href against base. Returns None for non-http(s) URLs."""
    try:
        resolved = urljoin(base, href)
        parsed = urlparse(resolved)
        if parsed.scheme not in ("http", "https"):
            return None
        return resolved
    except Exception:
        return None


def matches_any_pattern(url: str, patterns: list[str]) -> bool:
    """Return True if url matches any of the provided regex patterns."""
    for pattern in patterns:
        try:
            if re.search(pattern, url):
                return True
        except re.error:
            pass
    return False


def url_to_filepath_parts(url: str) -> list[str]:
    """
    Convert a URL path into a list of filesystem-safe path components.
    e.g. https://example.com/blog/post-1?id=2 → ['example.com', 'blog', 'post-1']
    """
    parsed = urlparse(url)
    domain = re.sub(r"[^\w.-]", "_", parsed.netloc)
    path_parts = [
        re.sub(r"[^\w.-]", "_", p)
        for p in parsed.path.strip("/").split("/")
        if p
    ]
    return [domain] + path_parts
