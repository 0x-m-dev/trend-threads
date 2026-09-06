#!/usr/bin/env python3
"""Daily trend scrape — Reddit, Hacker News, news RSS (+ Google Trends best-effort).

Stdlib only (urllib/json/xml). No keys, no deps.
Usage: python3 scripts/scrape.py [YYYY-MM-DD]  (default: today)
Output: data/<date>/trends.json. Exit 0 only with >=10 topics from >=2 sources.
"""
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

SOURCES = {
    "reddit": "https://www.reddit.com/hot.json?limit=20",
    "hackernews_ids": "https://hacker-news.firebaseio.com/v0/topstories.json",
}
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
]
UA = {"User-Agent": "trend-threads/1.0 (hermes-studio)"}


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fetch_reddit():
    out = []
    try:
        data = get_json(SOURCES["reddit"])
        for post in data["data"]["children"][:8]:
            d = post["data"]
            out.append({"source": "reddit", "title": d.get("title", ""),
                        "url": "https://reddit.com" + d.get("permalink", ""),
                        "ups": d.get("ups", 0), "comments": d.get("num_comments", 0)})
    except Exception as e:
        print(f"reddit error: {e}")
    return out


def fetch_hn():
    out = []
    try:
        ids = get_json(SOURCES["hackernews_ids"])[:8]
        for sid in ids:
            try:
                s = get_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=8)
                if s and s.get("title"):
                    out.append({"source": "hacker_news", "title": s["title"],
                                "url": s.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                                "points": s.get("score", 0)})
            except Exception:
                continue
    except Exception as e:
        print(f"hn error: {e}")
    return out


def fetch_rss():
    out = []
    for feed in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
            for item in root.iter("item"):
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                if title:
                    out.append({"source": "news", "title": title, "url": link})
                if len([t for t in out if t["source"] == "news"]) >= 6:
                    break
        except Exception as e:
            print(f"rss error ({feed}): {e}")
    return out[:6]


def fetch_gtrends():
    """Best-effort via keyless firecrawl. Failure is fine — other sources cover."""
    out = []
    try:
        r = subprocess.run(["npx", "-y", "firecrawl-cli@latest", "search",
                            "trending topics today", "--limit", "5"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip().strip("'\"")
                if line.startswith("http"):
                    out.append({"source": "google_trends", "title": line.split("://", 1)[-1].split("/")[0],
                                "url": line})
                if len(out) >= 4:
                    break
    except Exception as e:
        print(f"gtrends skipped: {e}")
    return out


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    from pathlib import Path
    trends = {"reddit": fetch_reddit(), "hacker_news": fetch_hn(),
              "news": fetch_rss(), "google_trends": fetch_gtrends()}
    total = sum(len(v) for v in trends.values())
    hit_sources = sum(1 for v in trends.values() if v)
    ddir = Path(__file__).resolve().parent.parent / "data" / day
    ddir.mkdir(parents=True, exist_ok=True)
    (ddir / "trends.json").write_text(json.dumps(trends, indent=2))
    print(f"scraped {day}: {total} topics from {hit_sources} sources → data/{day}/trends.json")
    if total < 10 or hit_sources < 2:
        print("ACCEPTANCE FAIL: need >=10 topics from >=2 sources")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
