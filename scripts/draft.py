#!/usr/bin/env python3
"""
Trend Threads — ICUMI-style TLDR posts with cross-refs.

Instead of long threads, produce one "In Case You Missed It" post per day
with a single "sweet" (highlight) topic, related HN links, and X tweet refs.

Output: data/<date>/icumi.md (single post) + data/<date>/icumi.json (structured)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import build_mock_post, summarize_items

OUTPUT_DIR = Path(__file__).parent.parent / "data" / date.today().isoformat()
TRENDS_FILE = OUTPUT_DIR / "trends.json"
ICUMI_FILE = OUTPUT_DIR / "icumi.md"
ICUMI_JSON = OUTPUT_DIR / "icumi.json"


# --- Topic helpers ---

def normalize_title(title: str) -> str:
    """Lowercase, strip HTML/CDATA artifacts, collapse whitespace."""
    t = re.sub(r'<!\[\[CDATA\|\]\]>', '', title)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&#8217;', "'", t)
    t = re.sub(r'&#8221;', '"', t)
    t = re.sub(r'&#8216;', "'", t)
    t = re.sub(r'[–—]', ' - ', t)
    return ' '.join(t.split()).strip()


def flatten_trends(data: dict) -> list[dict]:
    """Flatten scrape.py's per-source dict into a single sorted list."""
    flat = []
    for source, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            entry = {
                "source": source,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "score": item.get("points") or item.get("ups") or 0,
            }
            flat.append(entry)
    return sorted(flat, key=lambda t: t.get("score", 0), reverse=True)


def pick_highlight(trends: list[dict]) -> dict:
    """Pick the #1 highest-scored topic as the ICUMI highlight."""
    return trends[0] if trends else {}


def pick_related(trends: list[dict], count: int = 4, exclude_idx: int = 0) -> list[dict]:
    """Pick diverse related topics (not the highlight)."""
    selected = []
    used_titles = set()
    highlight = trends[exclude_idx]
    highlight_keys = set(re.findall(r'\b\w{4,}\b', normalize_title(highlight["title"]))) if highlight else set()

    for item in trends:
        if len(selected) >= count:
            break
        if item is trends[exclude_idx]:
            continue
        title = normalize_title(item["title"])
        keys = set(re.findall(r'\b\w{4,}\b', title))
        # Avoid heavy overlap with highlight
        if keys & highlight_keys:
            continue
        if title.lower() not in used_titles and len(selected) < count:
            selected.append(item)
            used_titles.add(title.lower())
    return selected


def extract_keywords(title: str, count: int = 3) -> list[str]:
    """Extract 2-4 word keywords from title for X search."""
    words = re.findall(r'\b\w{3,}\b', normalize_title(title))
    # Pick longest meaningful words, up to count
    picked = []
    for w in sorted(words, key=len, reverse=True):
        if len(w) >= 3 and w.lower() not in {"https", "http", "this", "that", "with", "from"}:
            picked.append(w)
        if len(picked) >= count:
            break
    return picked[:count]


# --- ICUMI drafting ---

def format_icumi_text(title: str) -> str:
    """Clean title for use in ICUMI."""
    return format_tweet(title)


def format_tweet(text: str) -> str:
    """Normalize text — clean artifacts."""
    t = re.sub(r'<!\[\[CDATA\|\]\]>', '', text)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&#8217;', "'", t)
    t = re.sub(r'&#8221;', '"', t)
    t = re.sub(r'&#8216;', "'", t)
    return ' '.join(t.split()).strip()


def build_icumi(
    highlight: dict,
    related: list[dict],
    x_refs: dict[str, list[dict]],
    mock_post: dict | None = None,
    summaries: list[dict] | None = None,
) -> str:
    """Build a single ICUMI-style post."""
    lines = []

    if not highlight:
        return "📡 No trends found today. Run scrape.py first."

    # Title / header
    highlight_title = format_icumi_text(highlight["title"])
    score = highlight.get("score", "")
    source = highlight.get("source", "")

    if score and score > 0:
        extra = f" ({score} pts)"
    elif source:
        extra = f" — {source}"
    else:
        extra = ""

    # ICUMI header
    lines.append(f"📡 In Case You Missed It")
    lines.append(f"📅 {date.today().strftime('%A, %B %d, %Y')}")
    lines.append("")

    # Highlight (single sweet)
    lines.append(f"🔥 **{highlight_title}{extra}**")

    # HN link if available
    if highlight.get("url"):
        lines.append(f"   📎 {highlight['url']}")
    lines.append("")

    # Related topics with links
    if related:
        lines.append("📌 Also trending:")
        for item in related:
            title = format_icumi_text(item["title"])
            pts = item.get("points") or item.get("ups") or ""
            url = item.get("url", "")
            if pts:
                lines.append(f"  • {title} ({pts} pts)")
            else:
                lines.append(f"  • {title}")
            if url:
                lines.append(f"    {url}")
        lines.append("")

    if summaries:
        lines.append("🧠 Article summaries:")
        for row in summaries:
            title = format_icumi_text(row.get("title", ""))
            summary = (row.get("summary") or "").strip()
            if title and summary and summary != title:
                lines.append(f"  • {title}")
                lines.append(f"    {summary}")
        lines.append("")

    if mock_post and mock_post.get("text"):
        lines.append("🐦 Mock post (copy to X):")
        lines.append("")
        lines.append(mock_post["text"])
        lines.append("")
        if mock_post.get("short"):
            lines.append(f"280-char hook ({mock_post.get('short_chars', len(mock_post['short']))} chars):")
            lines.append(mock_post["short"])
            lines.append("")

    # X tweet cross-refs
    all_topics = [highlight["title"]] + [r["title"] for r in related]
    topic_x_refs = {}
    for topic in all_topics:
        keyword = topic.strip()[:60]
        if keyword in x_refs and x_refs[keyword]:
            topic_x_refs[keyword] = x_refs[keyword]

    if topic_x_refs:
        lines.append("🐦 On X:")
        for topic, tweets in topic_x_refs.items():
            lines.append(f"  **{topic}:**")
            for tw in tweets[:3]:
                lines.append(f"    <{tw['url']}>")
        lines.append("")

    # Source summary
    lines.append("---")
    lines.append(f"📊 Sources: HN · Reddit · News · Google Trends")
    lines.append(f"🔗 Full archive: https://0x-m-dev.github.io/trend-threads/")

    return "\n".join(lines).strip()


def build_icumi_json(
    highlight: dict,
    related: list[dict],
    x_refs: dict[str, list[dict]],
    mock_post: dict | None = None,
    summaries: list[dict] | None = None,
) -> dict:
    """Structured JSON for render.py to consume."""
    return {
        "date": date.today().isoformat(),
        "highlight": highlight,
        "related": related,
        "x_refs": {k: v for k, v in list(x_refs.items())[:3]},  # limit for size
        "summaries": summaries or [],
        "mock_post": mock_post or {},
        "total_trends": 1 + len(related),
    }


# --- Main ---

def main() -> int:
    if not TRENDS_FILE.exists():
        print(f"ERROR: {TRENDS_FILE} not found. Run scrape.py first.", file=sys.stderr)
        return 1

    with open(TRENDS_FILE) as f:
        data = json.load(f)

    trends = flatten_trends(data)
    if len(trends) < 3:
        print(f"ERROR: Only {len(trends)} trends, need ≥3 to draft ICUMI.", file=sys.stderr)
        return 1

    # Pick highlight (top) + related
    highlight = pick_highlight(trends)
    related = pick_related(trends, count=4)

    # Fetch X tweet refs for highlight + related topics
    x_topics = [highlight["title"]] + [r["title"] for r in related]
    print(f"Fetching X refs for {len(x_topics)} topics...")
    x_refs = {}
    from scrape import fetch_x_tweets_for_topics  # dynamic import to avoid circular
    try:
        x_refs = fetch_x_tweets_for_topics(x_topics)
        print(f"Found X refs for {len(x_refs)} topics")
    except Exception as e:
        print(f"X refs skipped: {e}")

    print("Summarizing articles...")
    summaries = summarize_items([highlight, *related])
    mock_post = build_mock_post(highlight, related, summaries)

    # Build ICUMI post
    icumi_text = build_icumi(highlight, related, x_refs, mock_post=mock_post, summaries=summaries)
    icumi_data = build_icumi_json(
        highlight, related, x_refs, mock_post=mock_post, summaries=summaries
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (ICUMI_FILE).write_text(icumi_text)
    (ICUMI_JSON).write_text(json.dumps(icumi_data, indent=2))

    print(f"ICUMI post drafted — {ICUMI_FILE}")
    print(f"  Highlight: {highlight['title'][:60]}")
    print(f"  Related: {len(related)} topics")
    print(f"  X refs: {sum(len(v) for v in x_refs.values())} tweets")
    print(f"  JSON: {ICUMI_JSON}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
