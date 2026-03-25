from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class CookieConfig(BaseModel):
    name: str
    value: str
    domain: str = ""
    path: str = "/"
    secure: bool = False
    http_only: bool = False


class AuthConfig(BaseModel):
    type: Literal["none", "cookie", "form", "header"] = "none"
    # cookie auth
    cookies: List[CookieConfig] = Field(default_factory=list)
    # form auth
    login_url: Optional[str] = None
    username_selector: str = "#username"
    password_selector: str = "#password"
    submit_selector: str = "button[type=submit]"
    username: Optional[str] = None
    password: Optional[str] = None
    success_selector: Optional[str] = None
    # header auth
    headers: Dict[str, str] = Field(default_factory=dict)


class PaginationConfig(BaseModel):
    enabled: bool = True
    mode: Literal["auto", "scroll", "load_more", "url_pattern"] = "auto"
    max_pages: int = 10
    load_more_selector: Optional[str] = None
    url_pattern: Optional[str] = None   # e.g. "?page={n}" or "/page/{n}/"
    scroll_pause: float = 2.0


class UrlFiltersConfig(BaseModel):
    include_domains: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)


class ExtractionConfig(BaseModel):
    content_filter: Literal["none", "bm25", "pruning"] = "pruning"
    bm25_threshold: float = 1.2
    css_selector: Optional[str] = None
    exclude_selectors: List[str] = Field(default_factory=list)
    include_images: bool = False
    include_links: bool = True


class OutputConfig(BaseModel):
    filename_strategy: Literal["slug", "hash", "url_path"] = "slug"
    overwrite: bool = False
    add_frontmatter: bool = True
    extra_frontmatter_fields: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------

class CrawlerConfig(BaseModel):
    # Core
    start_url: str = ""
    depth: int = 2
    output_dir: str = "./crawled"
    max_pages: int = 200
    concurrency: int = 5
    delay_between_requests: float = 1.0
    respect_robots_txt: bool = True
    user_agent: str = (
        "Mozilla/5.0 (compatible; WebCrawler/1.0; +https://github.com/web-crawler)"
    )
    log_level: str = "INFO"

    # Rendering
    adaptive_rendering: bool = True
    force_js: bool = False
    force_static: bool = False

    # JS rendering settings
    js_timeout: int = 15000
    wait_for_selector: Optional[str] = None
    js_scroll_behavior: Literal["auto", "none", "custom"] = "auto"
    custom_js_snippet: Optional[str] = None

    # Sub-configs
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    url_filters: UrlFiltersConfig = Field(default_factory=UrlFiltersConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def check_force_exclusive(self) -> "CrawlerConfig":
        if self.force_js and self.force_static:
            raise ValueError("force_js and force_static cannot both be True")
        return self


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_config(
    config_path: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> CrawlerConfig:
    """Load config from YAML file (optional) then apply CLI overrides."""
    data: Dict[str, Any] = {}

    if config_path:
        path = Path(config_path)
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    if cli_overrides:
        # CLI flat keys override top-level config values
        data.update({k: v for k, v in cli_overrides.items() if v is not None})

    return CrawlerConfig(**data)
