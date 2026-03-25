from __future__ import annotations

from typing import Dict


def get_headers(auth_headers: Dict[str, str]) -> Dict[str, str]:
    """Return the auth headers dict to inject into BrowserConfig and httpx requests."""
    return dict(auth_headers)
