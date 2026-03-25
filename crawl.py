#!/usr/bin/env python3
"""
Web Crawler CLI — dynamic sites to structured Markdown.

Usage:
    python crawl.py --url https://example.com --depth 2 --output ./output
    python crawl.py --url https://example.com --config config.yaml --auth-type form
    docker-compose up (with START_URL and DEPTH env vars)
"""

import argparse
import asyncio
import sys

from utils.config_loader import load_config
from utils.logger import setup_root_logger


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crawl",
        description="Crawl dynamic websites and output structured Markdown files.",
    )
    p.add_argument("--url", metavar="URL", help="Starting URL to crawl")
    p.add_argument("--depth", type=int, metavar="N", help="Maximum crawl depth (default: 2)")
    p.add_argument("--output", metavar="DIR", help="Output directory for .md files (default: ./output)")
    p.add_argument("--config", metavar="FILE", help="Path to YAML config file")
    p.add_argument(
        "--auth-type",
        choices=["none", "cookie", "form", "header"],
        dest="auth_type",
        help="Authentication method",
    )
    p.add_argument("--max-pages", type=int, dest="max_pages", metavar="N", help="Hard cap on pages crawled")
    p.add_argument("--concurrency", type=int, metavar="N", help="Max parallel requests")
    p.add_argument("--no-js", action="store_true", dest="force_static", help="Force static extraction (no Playwright)")
    p.add_argument("--js", action="store_true", dest="force_js", help="Force JS rendering for all pages")
    p.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        dest="log_level",
        help="Logging verbosity (default: INFO)",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_root_logger(args.log_level)

    # Build CLI overrides dict (only non-None values)
    cli_overrides = {}
    if args.url:
        cli_overrides["start_url"] = args.url
    if args.depth is not None:
        cli_overrides["depth"] = args.depth
    if args.output:
        cli_overrides["output_dir"] = args.output
    if args.max_pages is not None:
        cli_overrides["max_pages"] = args.max_pages
    if args.concurrency is not None:
        cli_overrides["concurrency"] = args.concurrency
    if args.force_static:
        cli_overrides["force_static"] = True
    if args.force_js:
        cli_overrides["force_js"] = True
    if args.auth_type:
        cli_overrides["auth"] = {"type": args.auth_type}

    try:
        config = load_config(config_path=args.config, cli_overrides=cli_overrides)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not config.start_url:
        parser.print_help()
        print("\n[ERROR] --url is required (or set start_url in config file)", file=sys.stderr)
        sys.exit(1)

    # Import here to keep startup fast if --help is requested
    from crawler.orchestrator import Orchestrator

    orchestrator = Orchestrator(config)
    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
