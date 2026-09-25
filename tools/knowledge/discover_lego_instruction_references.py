#!/usr/bin/env python3
"""Discover official LEGO building-instruction PDF URLs for sets containing minifigures.

Input:
  physical_samples.jsonl from ingest_lego_minifigure_references.py

The script extracts unique set numbers from each figure's set_occurrences, visits the
explicit LEGO Building Instructions page for each set, and records direct PDF URLs found
in the HTML. It does not download PDF bytes.

Output:
  lego_instruction_manifest.jsonl
  cache.sqlite3
  import_report.json

Use conservative delays. LEGO states that its instructions archive contains thousands of
sets but not every set ever made, so "no instructions found" is an expected state.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

PROCESSOR_VERSION = "lego-instruction-discovery/v1"
USER_AGENT = "PersonalAgentOS-LEGOReferenceResearch/1.0"
PDF_RE = re.compile(r'https?://[^"\'<>\\]+?\.pdf(?:\?[^"\'<>\\]*)?', re.I)
RELATIVE_PDF_RE = re.compile(r'(?:"|\')([^"\']+?\.pdf(?:\?[^"\']*)?)(?:"|\')', re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(kind: str, *parts: str) -> str:
    raw = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=False)
    return f"{kind}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def read_samples(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS page_cache(
          set_num TEXT PRIMARY KEY,
          source_url TEXT NOT NULL,
          status TEXT NOT NULL,
          http_status INTEGER,
          html TEXT,
          error TEXT,
          fetched_at TEXT NOT NULL
        );
        """
    )


def fetch_page(conn: sqlite3.Connection, set_num: str, *, locale: str, timeout: float, delay: float, retries: int) -> tuple[str, str]:
    cached = conn.execute("SELECT status,html,error,source_url FROM page_cache WHERE set_num=?", (set_num,)).fetchone()
    if cached and cached[0] == "ok" and cached[1]:
        return cached[1], cached[3]

    source_url = f"https://www.lego.com/{locale}/service/building-instructions/{urllib.parse.quote(set_num)}"
    error = ""
    status_code: int | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                source_url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8", errors="replace")
                final_url = resp.geturl()
                conn.execute(
                    "INSERT OR REPLACE INTO page_cache VALUES(?,?,?,?,?,?,?)",
                    (set_num, final_url, "ok", status_code, body, None, now_iso()),
                )
                conn.commit()
                if delay:
                    time.sleep(delay)
                return body, final_url
        except urllib.error.HTTPError as exc:
            status_code = exc.code
            error = f"HTTP {exc.code}"
            retryable = exc.code in {429, 500, 502, 503, 504}
        except Exception as exc:
            error = str(exc)
            retryable = True
        if attempt < retries and retryable:
            time.sleep(max(1.0, delay) * (2 ** attempt))
            continue
        break

    conn.execute(
        "INSERT OR REPLACE INTO page_cache VALUES(?,?,?,?,?,?,?)",
        (set_num, source_url, "error", status_code, None, error[:2000], now_iso()),
    )
    conn.commit()
    raise RuntimeError(error)


def discover_pdfs(body: str, base_url: str) -> list[str]:
    decoded = html.unescape(body).replace("\\u002F", "/").replace("\\/", "/")
    urls = set(PDF_RE.findall(decoded))
    for relative in RELATIVE_PDF_RE.findall(decoded):
        urls.add(urllib.parse.urljoin(base_url, relative))
    return sorted(
        url for url in urls
        if urllib.parse.urlparse(url).hostname
        and (
            urllib.parse.urlparse(url).hostname.endswith("lego.com")
            or urllib.parse.urlparse(url).hostname.endswith("assets.lego.com")
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--locale", default="en-us")
    ap.add_argument("--delay-seconds", type=float, default=0.75)
    ap.add_argument("--timeout-seconds", type=float, default=30.0)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    set_to_samples: dict[str, set[str]] = {}
    for sample in read_samples(args.samples.resolve()):
        sample_id = str(sample.get("sample_id") or "")
        for occ in sample.get("set_occurrences") or []:
            set_num = str(occ.get("set_num") or "")
            if set_num:
                set_to_samples.setdefault(set_num, set()).add(sample_id)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(out / "cache.sqlite3")
    init_db(conn)

    manifest_path = out / "lego_instruction_manifest.jsonl"
    discovered = 0
    sets_checked = 0
    sets_with_pdf = 0
    errors: list[dict[str, str]] = []

    with manifest_path.open("w", encoding="utf-8") as mf:
        for set_num in sorted(set_to_samples):
            if args.limit is not None and sets_checked >= args.limit:
                break
            sets_checked += 1
            try:
                body, source_url = fetch_page(
                    conn, set_num, locale=args.locale, timeout=args.timeout_seconds,
                    delay=args.delay_seconds, retries=args.retries,
                )
                pdfs = discover_pdfs(body, source_url)
                if pdfs:
                    sets_with_pdf += 1
                for pdf_url in pdfs:
                    record = {
                        "reference_asset_id": stable_id("instruction", set_num, pdf_url),
                        "medium": "official_building_instruction_pdf",
                        "authority": "lego_primary",
                        "set_num": set_num,
                        "related_sample_ids": sorted(set_to_samples[set_num]),
                        "source_page_url": source_url,
                        "source_url": pdf_url,
                        "source_role": "building_instruction",
                        "materialized_locally": False,
                        "retrieved_at": now_iso(),
                        "processor_version": PROCESSOR_VERSION,
                    }
                    mf.write(json.dumps(record, ensure_ascii=False) + "\n")
                    discovered += 1
            except Exception as exc:
                errors.append({"set_num": set_num, "error": str(exc)[:500]})

    report = {
        "schema": "lego-instruction-discovery-report/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": now_iso(),
        "unique_sets_in_input": len(set_to_samples),
        "sets_checked": sets_checked,
        "sets_with_pdf": sets_with_pdf,
        "instruction_pdf_records": discovered,
        "errors": len(errors),
        "error_examples": errors[:100],
        "manifest": str(manifest_path),
        "policy": "Discovers direct URLs from explicit LEGO instruction pages; does not download PDFs.",
        "next_stage": "Materialize selected PDFs locally, render/extract likely minifigure pages, detect/crop figure art, and link derived images back to the PDF/page.",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    conn.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
