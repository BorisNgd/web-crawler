from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from slugify import slugify

from crawler.trafilatura_runner import ExtractionResult
from output import frontmatter, md_cleaner
from utils.logger import get_logger
from utils.url_utils import url_to_filepath_parts

if TYPE_CHECKING:
    from utils.config_loader import CrawlerConfig

logger = get_logger(__name__)

# Track used filenames to handle collisions: path → count
_used_names: Dict[str, int] = {}


def write(result: ExtractionResult, config: "CrawlerConfig") -> Optional[Path]:
    """
    Clean, assemble, and write a .md file for *result*.
    Returns the Path written, or None if nothing was written.
    """
    cleaned_md = md_cleaner.clean(
        result.raw_markdown,
        include_links=config.extraction.include_links,
    )

    if not cleaned_md:
        logger.debug("Skipping empty content for %s", result.url)
        return None

    out_dir = Path(config.output_dir)

    # Determine output file path
    filepath = _resolve_filepath(result, out_dir, config)

    if filepath.exists() and not config.output.overwrite:
        logger.debug("Skipping existing file %s", filepath)
        return filepath

    # Assemble final content
    if config.output.add_frontmatter:
        fm = frontmatter.build(result, extra_fields=config.output.extra_frontmatter_fields or {})
        content = fm + "\n" + cleaned_md + "\n"
    else:
        content = cleaned_md + "\n"

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    logger.info("Wrote %s (%d words)", filepath, result.raw_markdown.count(" "))
    return filepath


def _resolve_filepath(result: ExtractionResult, out_dir: Path, config: "CrawlerConfig") -> Path:
    strategy = config.output.filename_strategy
    domain = _safe_domain(result.url)

    if strategy == "slug":
        base_name = _slug_name(result)
        subdir = out_dir / domain
    elif strategy == "hash":
        base_name = hashlib.md5(result.url.encode()).hexdigest()[:12]
        subdir = out_dir / domain
    else:  # url_path
        parts = url_to_filepath_parts(result.url)
        subdir = out_dir / Path(*parts[:-1]) if len(parts) > 1 else out_dir
        base_name = parts[-1] if parts else "index"

    return _unique_path(subdir, base_name)


def _slug_name(result: ExtractionResult) -> str:
    """Generate a filesystem-safe slug from the page title or URL path."""
    source = result.title or ""
    if not source:
        from urllib.parse import urlparse
        path = urlparse(result.url).path.strip("/")
        source = path.replace("/", "-") or "index"
    slug = slugify(source, max_length=80, word_boundary=True, separator="-")
    return slug or "page"


def _safe_domain(url: str) -> str:
    from urllib.parse import urlparse
    netloc = urlparse(url).netloc.lower()
    return re.sub(r"[^\w.-]", "_", netloc)


def _unique_path(directory: Path, base_name: str) -> Path:
    """Return a unique .md path, appending _2, _3 etc. on collision."""
    key = str(directory / base_name)
    count = _used_names.get(key, 0) + 1
    _used_names[key] = count

    if count == 1:
        return directory / f"{base_name}.md"
    return directory / f"{base_name}_{count}.md"


def reset_name_registry() -> None:
    """Clear the collision-tracking registry (call between crawl sessions)."""
    _used_names.clear()
