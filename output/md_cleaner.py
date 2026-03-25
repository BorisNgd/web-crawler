from __future__ import annotations

import html
import re


# More than 2 consecutive blank lines → 2
_MULTI_BLANK = re.compile(r"\n{3,}")
# Lines that are purely a URL (navigation artifacts from Crawl4AI)
_BARE_URL_LINE = re.compile(r"^\s*https?://\S+\s*$", re.MULTILINE)
# Trailing whitespace on each line
_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)
# Collapse multiple spaces inside a line (not leading)
_MULTI_SPACE = re.compile(r"(?<=\S)  +")
# Markdown link text with excessive whitespace: [  text  ](url)
_LINK_WS = re.compile(r"\[\s+([^\]]+?)\s+\]\(")


def clean(markdown: str, include_links: bool = True) -> str:
    """Post-process raw Crawl4AI / Trafilatura Markdown output."""
    if not markdown:
        return ""

    # Decode HTML entities
    text = html.unescape(markdown)

    # Remove bare URL lines (navigation artifacts)
    text = _BARE_URL_LINE.sub("", text)

    # Strip trailing whitespace
    text = _TRAILING_WS.sub("", text)

    # Normalise link text whitespace
    text = _LINK_WS.sub(r"[\1](", text)

    # Collapse excessive spaces within lines
    text = _MULTI_SPACE.sub(" ", text)

    # Collapse excessive blank lines
    text = _MULTI_BLANK.sub("\n\n", text)

    # Optionally strip all markdown links
    if not include_links:
        # Replace [text](url) with just text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Ensure heading hierarchy: if no H1 exists, promote first H2 to H1
    text = _fix_heading_hierarchy(text)

    return text.strip()


def _fix_heading_hierarchy(text: str) -> str:
    """If there is no H1, promote the first H2 to H1."""
    has_h1 = bool(re.search(r"^# [^\n#]", text, re.MULTILINE))
    if has_h1:
        return text

    # Find first H2 and promote it
    promoted = False

    def promote_first(m: re.Match) -> str:
        nonlocal promoted
        if not promoted:
            promoted = True
            return "# " + m.group(1)
        return m.group(0)

    return re.sub(r"^## (.+)$", promote_first, text, flags=re.MULTILINE)
