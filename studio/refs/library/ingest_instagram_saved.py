#!/usr/bin/env python3
"""Ingest Instagram Saved Reel URLs (official JSON export or plain-text URL list) into 01_references.csv.

Zero scraping, zero credentials required.
Supported inputs:
  1. Instagram's official "Download Your Information" JSON (`saved_posts.json` or `saved_collections.json`)
  2. A plain `.txt` / `.csv` list of Instagram Reel URLs (one URL per line; `# Collection Name` headers supported)

Usage:
  python studio/refs/library/ingest_instagram_saved.py --input saved_posts.json --csv studio/refs/library/01_references.csv
  python studio/refs/library/ingest_instagram_saved.py --input urls.txt --collection "Combat" --csv studio/refs/library/01_references.csv
  python studio/refs/library/ingest_instagram_saved.py --score 5 5 5 4 4
"""
import argparse
import csv
import datetime
import json
import pathlib
import re

URL_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[A-Za-z0-9_\-]+/?")

HEADERS = [
    "reference_id", "instagram_url", "creator_username", "saved_collection",
    "date_added", "access_status", "primary_category", "secondary_tags",
    "subject", "timestamps_reviewed", "analysis_status", "priority_score",
    "mahabharata_scene_idea", "notes", "rights_notes",
]


def normalize_url(url: str) -> str:
    m = URL_RE.search(url.strip())
    if not m:
        return url.strip().split("?")[0]
    u = m.group(0)
    return u if u.endswith("/") else u + "/"


def parse_instagram_json(path: pathlib.Path, default_collection: str):
    """Parse Meta/Instagram official `saved_posts.json` or `saved_collections.json`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []

    def handle_entry(item, collection_name):
        sm = item.get("string_map_data") or {}
        url = ""
        creator = item.get("title", "") or ""
        ts = ""
        for k, v in sm.items():
            if not isinstance(v, dict):
                continue
            href = v.get("href", "")
            val = v.get("value", "")
            if "instagram.com" in href:
                url = href
            elif "instagram.com" in str(val):
                url = str(val)
            if not creator and k.lower() in ("name", "author", "creator") and val:
                creator = str(val)
            if v.get("timestamp"):
                ts = datetime.datetime.fromtimestamp(v["timestamp"], datetime.timezone.utc).strftime("%Y-%m-%d")
        if url:
            records.append((normalize_url(url), creator.lstrip("@"), collection_name, ts))

    if isinstance(data, dict):
        for key in ("saved_saved_media", "saved_saved_collections"):
            items = data.get(key, [])
            if isinstance(items, list):
                cur_col = default_collection
                for it in items:
                    if isinstance(it, dict):
                        if "string_map_data" in it:
                            col = (it.get("string_map_data", {}).get("Name", {}) or {}).get("value") or cur_col
                            if "saved_collections" in key and not any("instagram.com" in str(v.get("href", "")) for v in it["string_map_data"].values() if isinstance(v, dict)):
                                cur_col = col
                                continue
                            handle_entry(it, cur_col)
                        for sub in it.get("media", []) or []:
                            handle_entry(sub, cur_col)
    elif isinstance(data, list):
        for it in data:
            if isinstance(it, dict):
                handle_entry(it, default_collection)
    return records


def parse_text_urls(path: pathlib.Path, default_collection: str):
    """Parse pasted URLs from a .txt file (supports `# Collection Name` section headers)."""
    records = []
    cur_col = default_collection
    today = datetime.date.today().isoformat()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            cur_col = s.lstrip("#").strip() or cur_col
            continue
        for match in URL_RE.findall(s):
            records.append((normalize_url(match), "", cur_col, today))
    return records


def compute_priority(v: float, r: float, m: float, f: float, c: float) -> float:
    return round(0.30 * v + 0.25 * r + 0.20 * m + 0.15 * f + 0.10 * c, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Path to saved_posts.json, saved_collections.json, or urls.txt")
    ap.add_argument("--csv", default="studio/refs/library/01_references.csv")
    ap.add_argument("--collection", default="Uncategorised")
    ap.add_argument("--score", nargs=5, type=float, metavar=("V", "R", "M", "F", "C"),
                    help="Compute priority score P = 0.30V + 0.25R + 0.20M + 0.15F + 0.10C")
    args = ap.parse_args()

    if args.score:
        p = compute_priority(*args.score)
        print(f"Priority Score P = {p} / 5.00")
        return

    if not args.input:
        ap.error("--input or --score is required")

    in_path = pathlib.Path(args.input)
    csv_path = pathlib.Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    existing_rows = []
    seen_urls = set()
    max_id = 0
    if csv_path.exists():
        with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
        if reader:
            for row in reader[1:]:
                if not any(cell.strip() for cell in row):
                    continue
                url_val = row[1].strip() if len(row) > 1 else ""
                if row[0].startswith("REF-") and row[0][4:].isdigit():
                    max_id = max(max_id, int(row[0][4:]))
                # Drop blank starter placeholder row when real URLs are added
                if row[0] == "REF-0001" and not url_val:
                    continue
                if url_val:
                    seen_urls.add(normalize_url(url_val))
                existing_rows.append(row)

    if in_path.suffix.lower() == ".json":
        parsed = parse_instagram_json(in_path, args.collection)
    else:
        parsed = parse_text_urls(in_path, args.collection)

    added = 0
    next_id = max(1, max_id + 1 if seen_urls else 1)
    for url, creator, col, dt in parsed:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        ref_id = f"REF-{next_id:04d}"
        next_id += 1
        existing_rows.append([
            ref_id, url, creator, col, dt, "NEEDS_REVIEW", "", "", "", "", "PENDING", "", "", "", ""
        ])
        added += 1

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        w.writerows(existing_rows)

    print(f"Ingested {added} new Reels (total {len(existing_rows)} records) -> {csv_path}")


if __name__ == "__main__":
    main()
