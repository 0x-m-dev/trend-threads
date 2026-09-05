#!/usr/bin/env python3
"""
Trend Threads — Multi-source trend scraper.

Fetches trending topics from:
  - Hacker News (top stories API)
  - RSS feeds (BBC, HN frontpage via hnrss, etc.)
  - Google Trends (via Firecrawl CLI, best-effort)

Outputs: data/<YYYY-MM-DD>/trends.json
Acceptance: ≥10 topics from ≥2 sources, exit 0.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.parent / "data" / date.today().isoformat()

# RSS sources — each yields (title, url, source)
RSS_SOURCES: list[tuple[str, str]] = [
    ("Hacker News", "https://hnrss.org/frontpage"),
    ("BBC Top News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
]

# HN items with score ≥ this threshold are considered "trending"
HN_MIN_SCORE = 150
# Number of top HN story IDs to fetch
HN_TOP_N = 30

# ---------------------------------------------------------------------------
# RSS fetcher (regex-based — more robust than XML parsing for messy feeds)
# ---------------------------------------------------------------------------

def fetch_rss_feed(name: str, url: str) -> list[dict[str, Any]]:
    """Fetch an RSS feed and return list of {title, url, source}."""
    results: list[dict[str, Any]] = []
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "trend-threads/0.1.0 (Hermes Agent)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        # Strip namespace prefixes, remove CDATA wrappers
        raw = re.sub(r'<(\w*:)?(\w+)', r'<\2', raw)
        raw = re.sub(r'<!\[CDATA\[|\]\]>', '', raw)

        # Find <item>...</item> or <entry>...</entry> blocks
        blocks = re.findall(r'<(item|entry)>(.*?)</\1>', raw, re.DOTALL)

        for _, block in blocks:
            title_m = re.search(r'<title[^>]*>(.*?)</title>', block, re.DOTALL)
            link_m = re.search(r'<link[^>]*>(.*?)</link>', block, re.DOTALL)
            if not title_m:
                continue
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
            if len(title) < 10:
                continue
            url_val = ""
            if link_m:
                url_val = re.sub(r'<[^>]+>', '', link_m.group(1)).strip()
            results.append({
                "title": title,
                "url": url_val,
                "source": name,
            })
    except Exception as e:
        print(f"RSS WARN: {name} ({url}) failed: {e}", file=sys.stderr)

    return results

# ---------------------------------------------------------------------------
# Hacker News fetcher
# ---------------------------------------------------------------------------

def fetch_hn_top() -> list[dict[str, Any]]:
    """Fetch HN top stories and return trending items."""
    results: list[dict[str, Any]] = []
    try:
        top_resp = urllib.request.urlopen(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=15
        )
        top_ids: list[int] = json.loads(top_resp.read())[:HN_TOP_N]
    except Exception as e:
        print(f"HN WARN: top stories fetch failed: {e}", file=sys.stderr)
        return results

    for item_id in top_ids:
        try:
            item_resp = urllib.request.urlopen(
                f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                timeout=5,
            )
            data = json.loads(item_resp.read())
            if not data.get("title"):
                continue
            score = data.get("score", 0)
            if score < HN_MIN_SCORE:
                continue
            results.append({
                "title": data["title"],
                "url": data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                "source": "Hacker News",
                "score": score,
                "hn_id": item_id,
            })
        except Exception:
            continue

    return results

# ---------------------------------------------------------------------------
# Google Trends fetcher (via Firecrawl CLI)
# ---------------------------------------------------------------------------

def fetch_google_trends() -> list[dict[str, Any]]:
    """Fetch Google Trends via firecrawl CLI (best-effort)."""
    results: list[dict[str, Any]] = []
    try:
        proc = subprocess.run(
            ["npx", "-y", "firecrawl-cli@latest", "search",
             "Google Trends United States today"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            # Firecrawl may hit rate limits; that's OK — best-effort
            err = proc.stderr.strip()
            if "rate limit" in err.lower() or "api key" in err.lower():
                print("Google Trends: rate-limited (keyless tier). Skipping.", file=sys.stderr)
            else:
                print(f"Google Trends CLI error: {err[:200]}", file=sys.stderr)
            return results

        output = proc.stdout.strip()
        if not output:
            return results

        # Firecrawl returns markdown-like text; extract plausible headlines
        for line in output.splitlines():
            line = line.strip().lstrip("-•* ")
            if len(line) < 15 or line.startswith(("Error", "error", "You've")):
                continue
            # Clean up any markdown
            line = line.replace("**", "").replace("*", "").strip()
            results.append({
                "title": line,
                "url": "",
                "source": "Google Trends",
            })
    except FileNotFoundError:
        print("Google Trends: firecrawl CLI not found. Skipping.", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Google Trends: CLI timed out. Skipping.", file=sys.stderr)
    except Exception as e:
        print(f"Google Trends: error: {e}", file=sys.stderr)

    return results

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scrape() -> dict[str, Any]:
    """Run all scrapers and return combined results."""
    all_trends: list[dict[str, Any]] = []
    source_stats: dict[str, int] = {}

    # 1. Hacker News
    hn_items = fetch_hn_top()
    all_trends.extend(hn_items)
    source_stats["Hacker News"] = len(hn_items)

    # 2. RSS feeds
    for name, url in RSS_SOURCES:
        rss_items = fetch_rss_feed(name, url)
        all_trends.extend(rss_items)
        source_stats[name] = len(rss_items)

    # 3. Google Trends (best-effort)
    gt_items = fetch_google_trends()
    all_trends.extend(gt_items)
    source_stats["Google Trends"] = len(gt_items)

    # Deduplicate by title (fuzzy: strip punctuation/case)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for t in all_trends:
        key = t["title"].strip().lower().replace(".", "").replace(",", "")
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # Build output
    output = {
        "date": date.today().isoformat(),
        "sources": list(source_stats.keys()),
        "source_counts": source_stats,
        "total_trends": len(unique),
        "trends": unique,
    }

    return output


def main() -> int:
    """Entry point."""
    result = scrape()

    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "trends.json"

    # Write JSON
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Validation
    n_sources = len([s for s in result["source_counts"].values() if s > 0])
    n_trends = result["total_trends"]

    print(f"Trend Threads scrape — {n_trends} trends from {n_sources} sources")
    print(f"  → {output_file}")
    for src, count in result["source_counts"].items():
        if count > 0:
            print(f"  • {src}: {count}")

    if n_trends < 10 or n_sources < 2:
        print(f"\nWARNING: {n_trends} trends from {n_sources} sources "
              f"(need ≥10 from ≥2)", file=sys.stderr)
        # Still write output but return 1 for cron to flag
        return 1

    print(f"\n✓ Acceptance: {n_trends} trends ≥10, {n_sources} sources ≥2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
