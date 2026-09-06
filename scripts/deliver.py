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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from studio_ids import project_channel_id
REVIEW_CHANNEL_ID = project_channel_id("trend-threads")  # #trend-threads


def main() -> int:
    if not THREAD_FILE.exists():
        print(f"ERROR: {THREAD_FILE} not found. Run draft.py first.", file=sys.stderr)
        return 1

    with open(THREAD_FILE) as f:
        thread = f.read().strip()

    with open(TRENDS_FILE) as f:
        trends_data = json.load(f)

    if isinstance(trends_data, dict) and "total_trends" in trends_data:
        n_trends = trends_data.get("total_trends", 0)
        n_sources = len([s for s in trends_data.get("source_counts", {}).values() if s > 0])
    else:
        # dict-of-lists shape: {"reddit": [...], ...} (or {"trends": {...}})
        groups = trends_data.get("trends", trends_data) if isinstance(trends_data, dict) else []
        groups = groups.values() if isinstance(groups, dict) else groups
        groups = [g for g in groups if isinstance(g, list)]
        n_trends = sum(len(g) for g in groups)
        n_sources = len(groups)

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
