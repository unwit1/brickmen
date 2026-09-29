#!/usr/bin/env python3
"""Extract image URL candidates from a public product page for evidence acquisition.

The extractor is metadata-only: it fetches HTML, finds absolute/relative image URLs
and image-like URL strings embedded in attributes/JSON, normalizes HTML/JSON escaping,
and emits candidate URLs plus small context windows. It does not download image bytes
or approve any candidate.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = "BrickmenProductImageDiscovery/1.0"
VERSION = "product-image-candidate-extractor/v1"

URL_PATTERN = re.compile(
    r"""(?P<url>
        https?:(?:\\/\\/|//)[^"'<>\s]+
        |
        (?:(?:src|href|data-[\w-]+)\s*=\s*["'])
        (?P<relative>[^"'<>]+)
    )""",
    re.IGNORECASE | re.VERBOSE,
)
IMAGE_HINTS = (
    "/images/",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    "srcset",
    "zoom",
)


def normalize_candidate(raw: str, page_url: str) -> str | None:
    value = html.unescape(raw.strip())
    value = value.replace("\\/", "/")
    value = value.rstrip("),;]")
    if not value:
        return None
    if value.startswith("//"):
        value = "https:" + value
    elif not value.startswith(("http://", "https://")):
        value = urllib.parse.urljoin(page_url, value)
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    return value


def extract_candidates(
    page_url: str,
    html_text: str,
    *,
    contains: list[str] | None = None,
    context_chars: int = 180,
) -> list[dict[str, Any]]:
    needles = [needle.lower() for needle in (contains or []) if needle]
    found: dict[str, dict[str, Any]] = {}

    # Broad URL-like strings, including escaped JSON URLs.
    broad = re.compile(
        r"""(?:https?:)?(?:\\/\\/|//)[^"'<>\s]+|(?:https?://)[^"'<>\s]+""",
        re.IGNORECASE,
    )
    # Quoted attribute values catch relative image URLs and srcset strings.
    attrs = re.compile(
        r"""(?:src|href|srcset|data-[\w-]+)\s*=\s*(["'])(.*?)\1""",
        re.IGNORECASE | re.DOTALL,
    )

    spans: list[tuple[int, int, str]] = []
    for match in broad.finditer(html_text):
        spans.append((match.start(), match.end(), match.group(0)))
    for match in attrs.finditer(html_text):
        value = match.group(2)
        # srcset can hold comma-separated "URL width" entries.
        for part in value.split(","):
            token = part.strip().split()[0] if part.strip() else ""
            if token:
                start = match.start(2)
                spans.append((start, match.end(2), token))

    for start, end, raw in spans:
        url = normalize_candidate(raw, page_url)
        if not url:
            continue
        low = url.lower()
        if needles and not any(needle in low for needle in needles):
            continue
        if not needles and not any(hint in low for hint in IMAGE_HINTS):
            continue
        before = max(0, start - context_chars)
        after = min(len(html_text), end + context_chars)
        context = html.unescape(html_text[before:after]).replace("\\/", "/")
        row = found.setdefault(
            url,
            {
                "url": url,
                "occurrences": 0,
                "contexts": [],
            },
        )
        row["occurrences"] += 1
        if context not in row["contexts"] and len(row["contexts"]) < 3:
            row["contexts"].append(context)

    return sorted(
        found.values(),
        key=lambda row: (
            0 if "/images/" in row["url"].lower() else 1,
            row["url"],
        ),
    )


def fetch_page(
    page_url: str,
    *,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(page_url)
    if parsed.scheme.lower() != "https":
        raise ValueError("page URL must use HTTPS")
    if (parsed.hostname or "").lower() not in allowed_hosts:
        raise ValueError("page host is not allowlisted")

    request = urllib.request.Request(
        page_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        final_host = (
            urllib.parse.urlparse(final_url).hostname or ""
        ).lower()
        if final_host not in allowed_hosts:
            raise ValueError(f"redirected to non-allowlisted host: {final_host}")
        data = response.read(max_bytes + 1)
        charset = response.headers.get_content_charset() or "utf-8"
    if len(data) > max_bytes:
        raise ValueError(f"page exceeds max_bytes={max_bytes}")
    return data.decode(charset, errors="replace"), final_url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--contains", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024)
    args = parser.parse_args()

    allowed_hosts = {
        str(host).strip().lower()
        for host in args.allow_host
        if str(host).strip()
    }
    if not allowed_hosts:
        raise SystemExit("At least one --allow-host is required.")

    text, final_url = fetch_page(
        args.url,
        allowed_hosts=allowed_hosts,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )
    candidates = extract_candidates(
        final_url,
        text,
        contains=args.contains,
    )
    result = {
        "schema": "product-image-candidate-extraction/v1",
        "processor_version": VERSION,
        "page_url": args.url,
        "final_page_url": final_url,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "policy": (
            "Metadata-only discovery. Candidate URLs are not byte-verified "
            "and are not evaluation inputs."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            "candidate_count": len(candidates),
            "urls": [row["url"] for row in candidates],
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
