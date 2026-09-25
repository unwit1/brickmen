#!/usr/bin/env python3
"""Discover media URLs embedded in an explicit list of LEGO.com pages.

This is a non-crawling discovery tool: it visits only page URLs supplied in the input
JSONL/text file, extracts image/media/asset links from HTML, and writes a source manifest.
It does not follow links and does not download media bytes.

Useful for:
- LEGO press releases / downloadable media pages
- official game pages
- official film pages
- designer interviews / character pages
- product pages selected by higher-level manifests
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PROCESSOR_VERSION = "lego-page-media-discovery/v1"
USER_AGENT = "PersonalAgentOS-LEGOReferenceResearch/1.0"

MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".webm", ".zip", ".pdf"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(kind: str, *parts: str) -> str:
    raw = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=False)
    return f"{kind}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


class AssetParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.urls: set[tuple[str, str]] = set()

    def add(self, value: str | None, role: str) -> None:
        if not value:
            return
        for candidate in value.split(","):
            candidate = candidate.strip().split(" ")[0]
            if not candidate:
                continue
            url = urllib.parse.urljoin(self.base_url, html.unescape(candidate))
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                continue
            suffix = Path(parsed.path).suffix.lower()
            host = (parsed.hostname or "").lower()
            if suffix in MEDIA_EXTS or "assets.lego.com" in host or "/cdn/" in parsed.path:
                self.urls.add((url, role))

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag in {"img", "source", "video"}:
            self.add(data.get("src"), tag + "_src")
            self.add(data.get("srcset"), tag + "_srcset")
            self.add(data.get("poster"), tag + "_poster")
        elif tag == "a":
            self.add(data.get("href"), "anchor_asset")
        elif tag == "meta":
            key = (data.get("property") or data.get("name") or "").lower()
            if key in {"og:image", "twitter:image", "og:video", "twitter:player"}:
                self.add(data.get("content"), key)


def read_pages(path: Path) -> list[str]:
    pages: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if text.startswith("{"):
                obj = json.loads(text)
                url = obj.get("url") or obj.get("source_url") or obj.get("page_url")
            else:
                url = text
            if url:
                pages.append(str(url))
    return list(dict.fromkeys(pages))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--delay-seconds", type=float, default=0.75)
    ap.add_argument("--timeout-seconds", type=float, default=30.0)
    args = ap.parse_args()

    pages = read_pages(args.pages.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    asset_count = 0
    page_errors = 0

    with args.output.open("w", encoding="utf-8") as out:
        for page_url in pages:
            host = (urllib.parse.urlparse(page_url).hostname or "").lower()
            if not (host == "lego.com" or host.endswith(".lego.com")):
                page_errors += 1
                continue
            try:
                req = urllib.request.Request(
                    page_url,
                    headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
                )
                with urllib.request.urlopen(req, timeout=args.timeout_seconds) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                    final_url = resp.geturl()
                parser = AssetParser(final_url)
                parser.feed(body)
                for asset_url, role in sorted(parser.urls):
                    record = {
                        "reference_asset_id": stable_id("pageasset", final_url, asset_url, role),
                        "medium": "official_page_discovered_asset",
                        "authority": "lego_primary",
                        "source_page_url": final_url,
                        "source_url": asset_url,
                        "source_role": role,
                        "materialized_locally": False,
                        "retrieved_at": now_iso(),
                        "processor_version": PROCESSOR_VERSION,
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    asset_count += 1
            except Exception:
                page_errors += 1
            if args.delay_seconds:
                time.sleep(args.delay_seconds)

    print(json.dumps({
        "pages": len(pages),
        "assets_discovered": asset_count,
        "page_errors": page_errors,
        "output": str(args.output),
        "policy": "Explicit LEGO.com pages only; no recursive crawling; URL discovery only."
    }, indent=2))


if __name__ == "__main__":
    main()
