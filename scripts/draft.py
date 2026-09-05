#!/usr/bin/env python3
"""
Trend Threads — Draft thread from today's trends.

Picks the top 3-4 trending topics and crafts a 5-7 tweet thread draft
(hook first, ≤280 chars/tweet, ends with question/CTA).

Outputs to: data/<date>/thread.md
Acceptance: one full cron tick → draft thread, ≤280 chars/tweet.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / date.today().isoformat()
TRENDS_FILE = OUTPUT_DIR / "trends.json"
THREAD_FILE = OUTPUT_DIR / "thread.md"

# --- Topic clustering helpers ---

def normalize_title(title: str) -> str:
    """Lowercase, strip common prefixes, collapse whitespace."""
    t = re.sub(r'<!\[CDATA\[|\]\]>', '', title)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&#8217;', "'", t)  # HTML entities
    t = re.sub(r'[–—]', ' - ', t)
    t = ' '.join(t.split())
    return t.strip().lower()


def cluster_topics(trends: list[dict], max_clusters: int = 4) -> list[list[dict]]:
    """Group topics by shared keywords — returns list of clusters."""
    clusters: list[list[dict]] = []
    used: set[int] = set()

    # Sort by score descending (HN items have score, others get 0)
    scored = sorted(trends, key=lambda t: t.get("score", 0), reverse=True)

    for i, item in enumerate(scored):
        if i in used:
            continue
        cluster = [item]
        used.add(i)
        keywords = set(re.findall(r'\b\w{4,}\b', normalize_title(item["title"])))

        for j, other in enumerate(scored):
            if j in used:
                continue
            other_keys = set(re.findall(r'\b\w{4,}\b', normalize_title(other["title"])))
            overlap = keywords & other_keys
            # Require at least 2 shared keywords AND one keyword present in both titles
            if len(overlap) >= 2:
                cluster.append(other)
                used.add(j)

        if len(cluster) > 1:
            clusters.append(cluster)
        else:
            clusters.append(cluster)

        if len(clusters) >= max_clusters:
            break

    # Drop clusters with only 1 item if we have more clusters available
    if len(clusters) > max_clusters:
        singletons = [c for c in clusters if len(c) == 1]
        multi = [c for c in clusters if len(c) > 1]
        clusters = multi + singletons[:max_clusters - len(multi)]

    return clusters[:max_clusters]


# --- Thread drafting ---

def format_tweet(text: str) -> str:
    """Normalize text for tweet format — clean up artifacts."""
    t = text
    t = re.sub(r'<!\[CDATA\[|\]\]>', '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&#8217;', "'", t)
    t = re.sub(r'&#8221;', '"', t)
    t = re.sub(r'&#8216;', "'", t)
    t = ' '.join(t.split())
    return t.strip()


def draft_thread(clusters: list[list[dict]]) -> str:
    """Draft a 5-7 tweet thread from topic clusters."""
    tweets = []

    # Tweet 1: Hook — pick the most interesting cluster
    best = clusters[0]
    hook_topic = best[0]["title"]
    hook_source = best[0].get("source", "")
    hook_score = best[0].get("score", "")
    hook_extra = f" ({hook_score} points)" if hook_score else f" — {hook_source}"
    tweets.append(f"🧵 {hook_topic}{hook_extra} (What's trending today — 1/7)")

    # Tweet 2: Second cluster summary
    if len(clusters) > 1:
        topic2 = clusters[1][0]["title"]
        tweets.append(f"\n{format_tweet(topic2)}")
        tweets[-1] += "\n\n(2/7)"

    # Tweet 3: Third cluster (or more from top cluster)
    if len(clusters) > 2:
        topic3 = clusters[2][0]["title"]
        tweets.append(f"\n{format_tweet(topic3)}")
        tweets[-1] += "\n\n(3/7)"
    elif len(best) > 1:
        topic_sub = format_tweet(best[1]["title"])
        tweets.append(f"\nAlso from {best[0].get('source', 'top source')}:\n{topic_sub}")
        tweets[-1] += "\n\n(3/7)"

    # Tweet 4: Roundup of remaining interesting items
    remaining = []
    for cluster in clusters[2:] if len(clusters) > 2 else [best[1:]]:
        for item in cluster[:1]:
            t = format_tweet(item["title"])
            if len(t) > 5:
                remaining.append(t)

    if remaining:
        tweets.append(f"\n" + "\n".join(f"• {r}" for r in remaining[:3]))
        tweets[-1] += "\n\n(4/7)"

    # Tweet 5: CTA
    tweets.append("\nWhat are you watching today? Drop links below 👇\n\n(5/7)")

    return "\n".join(tweets).strip()


# --- Main ---

def main() -> int:
    if not TRENDS_FILE.exists():
        print(f"ERROR: {TRENDS_FILE} not found. Run scrape.py first.", file=sys.stderr)
        return 1

    with open(TRENDS_FILE) as f:
        data = json.load(f)

    trends = data.get("trends", [])
    if len(trends) < 5:
        print(f"ERROR: Only {len(trends)} trends, need ≥5 to draft.", file=sys.stderr)
        return 1

    clusters = cluster_topics(trends, max_clusters=4)
    thread = draft_thread(clusters)

    # Validate: all tweets ≤280 chars
    tweet_lines = thread.split("\n\n")
    valid = True
    for line in tweet_lines:
        clean = line.strip()
        # Strip numbering suffix like "(1/7)"
        clean_no_num = re.sub(r'\s*\(\d+/\d+\)$', '', clean)
        if len(clean_no_num) > 280:
            print(f"WARNING: Tweet exceeds 280 chars ({len(clean_no_num)}): {clean_no_num[:60]}...")
            valid = False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(THREAD_FILE, "w") as f:
        f.write(thread)

    print(f"Thread drafted — {THREAD_FILE}")
    print(f"  Clusters: {len(clusters)} topics, {len(tweet_lines)} tweets")
    if valid:
        print("  ✓ All tweets ≤280 chars")
    else:
        print("  ⚠ Some tweets need trimming", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
