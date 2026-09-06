#!/usr/bin/env python3
"""
Trend Threads — Discord delivery of ICUMI post.

Reads today's ICUMI data and outputs a ready-to-post Discord message.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / date.today().isoformat()
ICUMI_FILE = OUTPUT_DIR / "icumi.json"
ICUMI_TEXT_FILE = OUTPUT_DIR / "icumi.md"
TRENDS_FILE = OUTPUT_DIR / "trends.json"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from studio_ids import project_channel_id

# Fallback channel if registry lookup fails
_FALLBACK_CHANNEL = "1545903101024796762"  # #specs


def _get_review_channel() -> str:
    """Get review channel ID, falling back to known default."""
    try:
        return project_channel_id("trend-threads")
    except RuntimeError:
        return _FALLBACK_CHANNEL


def main() -> int:
    if not ICUMI_TEXT_FILE.exists() and not ICUMI_FILE.exists():
        print(f"ERROR: No ICUMI data found. Run draft.py first.", file=sys.stderr)
        return 1

    # Read structured data
    icumi_data = {}
    if ICUMI_FILE.exists():
        with open(ICUMI_FILE) as f:
            icumi_data = json.load(f)

    highlight = icumi_data.get("highlight", {})
    related = icumi_data.get("related", [])
    x_refs = icumi_data.get("x_refs", {})

    # Read the text version if it exists (nicer Discord formatting)
    if ICUMI_TEXT_FILE.exists():
        icumi_text = ICUMI_TEXT_FILE.read_text().strip()
        print(icumi_text)
        return 0

    # Build message from structured data
    h_title = highlight.get("title", "No highlight today")
    h_score = highlight.get("score", "")
    h_source = highlight.get("source", "")
    h_url = highlight.get("url", "")

    lines = [
        f"📡 **Trend Threads — {date.today().strftime('%B %d, %Y')}**",
        "",
        f"🔥 **{h_title}**" + (f" ({h_score} pts)" if h_score else f" — {h_source}"),
    ]

    if h_url:
        lines.append(f"📎 {h_url}")

    if related:
        lines.append("")
        lines.append("📌 **Also trending:**")
        for item in related:
            title = item.get("title", "")
            pts = item.get("points") or item.get("ups", "")
            url = item.get("url", "")
            line = f"• {title}" + (f" ({pts})" if pts else "")
            if url:
                line += f"\n  🔗 {url}"
            lines.append(line)

    if x_refs:
        lines.append("")
        lines.append("🐦 **On X:**")
        for topic, tweets in list(x_refs.items())[:3]:
            lines.append(f"**{topic}:**")
            for tw in tweets[:3]:
                lines.append(f"• <{tw['url']}>")

    lines.append("")
    lines.append(f"📊 {len(related) + 1} topics scraped · Full archive: https://0x-m-dev.github.io/trend-threads/")

    message = "\n".join(lines)
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
