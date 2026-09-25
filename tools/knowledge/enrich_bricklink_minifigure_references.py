#!/usr/bin/env python3
"""Enrich a physical minifigure census with BrickLink catalog/component image references.

BrickLink API access requires a user-created API key/token and registered endpoint IP.
Credentials are read ONLY from environment variables and are never written to output:

  BRICKLINK_CONSUMER_KEY
  BRICKLINK_CONSUMER_SECRET
  BRICKLINK_TOKEN
  BRICKLINK_TOKEN_SECRET

Input:
  physical_samples.jsonl produced by ingest_lego_minifigure_references.py

Output:
  bricklink_reference_manifest.jsonl
  bricklink_components.jsonl
  bricklink_cache.sqlite3
  import_report.json

The SQLite cache makes the job resumable and avoids repeating successful API requests.
This tool does not download image bytes; feed its image URLs into the controlled image
materializer after reviewing source policy.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import random
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

API_BASE = "https://api.bricklink.com/api/store/v1"
PROCESSOR_VERSION = "bricklink-reference-enrichment/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def q(value: str) -> str:
    return urllib.parse.quote(str(value), safe="~-._")


def stable_id(kind: str, *parts: str) -> str:
    raw = json.dumps([kind, *parts], ensure_ascii=False, separators=(",", ":"))
    return f"{kind}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def credentials() -> tuple[str, str, str, str]:
    names = [
        "BRICKLINK_CONSUMER_KEY",
        "BRICKLINK_CONSUMER_SECRET",
        "BRICKLINK_TOKEN",
        "BRICKLINK_TOKEN_SECRET",
    ]
    values = [os.environ.get(name, "") for name in names]
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise SystemExit("Missing BrickLink API environment variables: " + ", ".join(missing))
    return tuple(values)  # type: ignore[return-value]


def oauth_header(method: str, url: str, params: dict[str, str], creds: tuple[str, str, str, str]) -> str:
    consumer_key, consumer_secret, token, token_secret = creds
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_token": token,
        "oauth_nonce": hashlib.sha256(f"{time.time_ns()}-{random.random()}".encode()).hexdigest()[:32],
        "oauth_timestamp": str(int(time.time())),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_version": "1.0",
    }
    signed_params = {**params, **oauth}
    param_string = "&".join(
        f"{q(k)}={q(v)}" for k, v in sorted(signed_params.items(), key=lambda kv: (q(kv[0]), q(kv[1])))
    )
    base_string = "&".join([method.upper(), q(url), q(param_string)])
    signing_key = f"{q(consumer_secret)}&{q(token_secret)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth["oauth_signature"] = signature
    return "OAuth " + ", ".join(f'{q(k)}="{q(v)}"' for k, v in sorted(oauth.items()))


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            endpoint TEXT NOT NULL,
            response_json TEXT,
            status TEXT NOT NULL,
            http_status INTEGER,
            error TEXT,
            fetched_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS processed_figure (
            fig_num TEXT PRIMARY KEY,
            sample_id TEXT NOT NULL,
            processed_at TEXT NOT NULL
        );
        """
    )


def cached_get(
    conn: sqlite3.Connection,
    endpoint: str,
    params: dict[str, str],
    creds: tuple[str, str, str, str],
    *,
    delay: float,
    timeout: float,
    retries: int,
) -> Any:
    query = urllib.parse.urlencode(params)
    key = endpoint + ("?" + query if query else "")
    row = conn.execute(
        "SELECT response_json,status,error FROM api_cache WHERE cache_key=?", (key,)
    ).fetchone()
    if row and row[1] == "ok":
        return json.loads(row[0])

    url = API_BASE + endpoint
    full_url = url + ("?" + query if query else "")
    last_error = ""
    last_http: int | None = None

    for attempt in range(retries + 1):
        header = oauth_header("GET", url, params, creds)
        request = urllib.request.Request(
            full_url,
            headers={
                "Authorization": header,
                "Accept": "application/json",
                "User-Agent": "PersonalAgentOS-LEGOReferenceResearch/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO api_cache
                    (cache_key,endpoint,response_json,status,http_status,error,fetched_at)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (key, endpoint, json.dumps(payload), "ok", response.status, None, now_iso()),
                )
                conn.commit()
                if delay:
                    time.sleep(delay)
                return payload
        except urllib.error.HTTPError as exc:
            last_http = exc.code
            body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {body[:1000]}"
            retryable = exc.code in {429, 500, 502, 503, 504}
        except Exception as exc:
            last_error = str(exc)
            retryable = True

        if attempt < retries and retryable:
            time.sleep(max(delay, 1.0) * (2 ** attempt))
            continue
        break

    conn.execute(
        """
        INSERT OR REPLACE INTO api_cache
        (cache_key,endpoint,response_json,status,http_status,error,fetched_at)
        VALUES(?,?,?,?,?,?,?)
        """,
        (key, endpoint, None, "error", last_http, last_error[:2000], now_iso()),
    )
    conn.commit()
    raise RuntimeError(last_error)


def read_samples(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def flatten_subset_data(data: Any) -> Iterator[dict[str, Any]]:
    # BrickLink subsets are grouped into matching groups. Be defensive about
    # nesting so API representation changes do not silently lose records.
    if isinstance(data, dict):
        if "item" in data:
            yield data
        for value in data.values():
            yield from flatten_subset_data(value)
    elif isinstance(data, list):
        for value in data:
            yield from flatten_subset_data(value)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay-seconds", type=float, default=0.5)
    ap.add_argument("--timeout-seconds", type=float, default=30.0)
    ap.add_argument("--retries", type=int, default=4)
    args = ap.parse_args()

    creds = credentials()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    db_path = out / "bricklink_cache.sqlite3"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    refs: dict[str, dict[str, Any]] = {}
    components: dict[str, dict[str, Any]] = {}
    processed = 0
    errors: list[dict[str, str]] = []

    for sample in read_samples(args.samples.resolve()):
        if args.limit is not None and processed >= args.limit:
            break
        fig_num = str(sample.get("fig_num") or "")
        sample_id = str(sample.get("sample_id") or "")
        if not fig_num or not sample_id:
            continue

        done = conn.execute("SELECT 1 FROM processed_figure WHERE fig_num=?", (fig_num,)).fetchone()
        if done:
            processed += 1
            continue

        try:
            item_payload = cached_get(
                conn, f"/items/MINIFIG/{q(fig_num)}", {}, creds,
                delay=args.delay_seconds, timeout=args.timeout_seconds, retries=args.retries,
            )
            item = item_payload.get("data", {}) if isinstance(item_payload, dict) else {}
            image_url = item.get("image_url")
            if image_url:
                rid = stable_id("ref", "bricklink", "MINIFIG", fig_num, image_url)
                refs[rid] = {
                    "reference_asset_id": rid,
                    "sample_id": sample_id,
                    "component_id": None,
                    "medium": "physical_catalog_image",
                    "authority": "structured_catalog",
                    "source_catalog": "bricklink",
                    "source_url": image_url,
                    "source_role": "minifigure_catalog_image",
                    "bricklink_item_no": fig_num,
                    "retrieved_at": now_iso(),
                }

            subset_payload = cached_get(
                conn,
                f"/items/MINIFIG/{q(fig_num)}/subsets",
                {"break_subsets": "true"},
                creds,
                delay=args.delay_seconds,
                timeout=args.timeout_seconds,
                retries=args.retries,
            )
            subset_data = subset_payload.get("data", []) if isinstance(subset_payload, dict) else []
            for entry in flatten_subset_data(subset_data):
                item_obj = entry.get("item") or {}
                if item_obj.get("type") != "PART":
                    continue
                part_num = str(item_obj.get("no") or "")
                if not part_num:
                    continue
                color_id = int(entry.get("color_id") or 0)
                component_id = stable_id("component", "bricklink", fig_num, part_num, str(color_id))
                component = {
                    "component_id": component_id,
                    "sample_id": sample_id,
                    "fig_num": fig_num,
                    "source_catalog": "bricklink",
                    "part_num": part_num,
                    "part_name": item_obj.get("name"),
                    "color_id": color_id,
                    "quantity": entry.get("quantity"),
                    "extra_quantity": entry.get("extra_quantity"),
                    "match_no": entry.get("match_no"),
                }
                components[component_id] = component

                # Color-specific image endpoint is valuable for decorated heads/torsos/legs.
                try:
                    img_payload = cached_get(
                        conn,
                        f"/items/PART/{q(part_num)}/images/{color_id}",
                        {},
                        creds,
                        delay=args.delay_seconds,
                        timeout=args.timeout_seconds,
                        retries=args.retries,
                    )
                    img = img_payload.get("data", {}) if isinstance(img_payload, dict) else {}
                    part_image_url = img.get("image_url") or img.get("thumbnail_url")
                    if part_image_url:
                        rid = stable_id("ref", "bricklink", "PART", part_num, str(color_id), part_image_url)
                        refs[rid] = {
                            "reference_asset_id": rid,
                            "sample_id": sample_id,
                            "component_id": component_id,
                            "medium": "physical_component_catalog_image",
                            "authority": "structured_catalog",
                            "source_catalog": "bricklink",
                            "source_url": part_image_url,
                            "source_role": "color_specific_component_image",
                            "bricklink_item_no": part_num,
                            "bricklink_color_id": color_id,
                            "retrieved_at": now_iso(),
                        }
                except Exception as exc:
                    errors.append({"fig_num": fig_num, "part_num": part_num, "error": str(exc)[:500]})

            conn.execute(
                "INSERT OR REPLACE INTO processed_figure(fig_num,sample_id,processed_at) VALUES(?,?,?)",
                (fig_num, sample_id, now_iso()),
            )
            conn.commit()
        except Exception as exc:
            errors.append({"fig_num": fig_num, "error": str(exc)[:500]})
        processed += 1

    # Deterministically rebuild outputs from this run's resolved records.
    refs_path = out / "bricklink_reference_manifest.jsonl"
    comps_path = out / "bricklink_components.jsonl"
    with refs_path.open("w", encoding="utf-8") as f:
        for key in sorted(refs):
            f.write(json.dumps(refs[key], ensure_ascii=False) + "\n")
    with comps_path.open("w", encoding="utf-8") as f:
        for key in sorted(components):
            f.write(json.dumps(components[key], ensure_ascii=False) + "\n")

    report = {
        "schema": "bricklink-reference-enrichment-report/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": now_iso(),
        "processed_samples_this_invocation": processed,
        "reference_records_written_this_invocation": len(refs),
        "component_records_written_this_invocation": len(components),
        "errors_this_invocation": len(errors),
        "error_examples": errors[:100],
        "cache_db": str(db_path),
        "outputs": {
            "references": str(refs_path),
            "components": str(comps_path),
        },
        "credential_policy": "OAuth credentials read from environment only; never written to output.",
        "source_notes": [
            "BrickLink API requires an API consumer key/token and registered endpoint IP.",
            "Catalog Get Item exposes image_url; Get Subsets exposes included parts; Get Item Image provides color-specific item image URLs.",
            "Use conservative delays and retain the cache; do not treat repeated API calls as a bulk-download substitute."
        ],
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    conn.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
