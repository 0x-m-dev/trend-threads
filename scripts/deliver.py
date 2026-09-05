#!/usr/bin/env python3
"""
Trend Threads — Discord delivery.

Reads today's thread draft and outputs it to stdout as a ready-to-post
message. In production, the Hermes cron agent would deliver this to
the review channel. For testing, prints to stdout.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / date.today().isoformat()
THREAD_FILE = OUTPUT_DIR / "thread.md"
TRENDS_FILE = OUTPUT_DIR / "trends.json"
REVIEW_CHANNEL_ID = "1545903101024796762"  # #specs / approved ! — the review channel


def main() -> int:
    if not THREAD_FILE.exists():
        print(f"ERROR: {THREAD_FILE} not found. Run draft.py first.", file=sys.stderr)
        return 1

    with open(THREAD_FILE) as f:
        thread = f.read().strip()

    with open(TRENDS_FILE) as f:
        trends_data = json.load(f)

    n_trends = trends_data.get("total_trends", 0)
    n_sources = len([s for s in trends_data.get("source_counts", {}).values() if s > 0])

    # Build delivery message
    lines = [
        f"📊 **Trend Threads — {date.today().strftime('%B %d, %Y')}**",
        f"",
        f"Scraped **{n_trends} trends** from **{n_sources} sources**.",
        f"",
        f"---",
        f"",
        thread,
        f"",
        f"---",
        f"📎 `data/{date.today().isoformat()}/` — trends.json + thread.md",
        f"",
        f"🔁 Review → post to X manually, or skip.",
    ]

    message = "\n".join(lines)
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
