#!/usr/bin/env python3
"""Render a day's thread.md + trends.json into docs/ for GitHub Pages.

Usage: python3 scripts/render.py [YYYY-MM-DD]  (default: today)
Output: docs/index.html (archive) + docs/<date>/index.html.
GitHub Pages serves /docs free — push and the site updates.
Stdlib only.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"


def parse_tweets(text: str) -> list:
    text = re.sub(r"\r", "", text).strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        parts = lines if len(lines) > 1 else [text]
    return parts


def icumi_card(data: dict) -> str:
    """Render an ICUMI-style post as HTML."""
    highlight = data.get("highlight", {})
    related = data.get("related", [])
    x_refs = data.get("x_refs", {})
    date_str = data.get("date", "")

    if not highlight:
        return '<p class="no-data">No data for this date.</p>'

    h_title = html.escape(highlight.get("title", ""))
    h_score = highlight.get("score", 0)
    h_url = highlight.get("url", "")
    h_source = highlight.get("source", "")

    score_html = f'<span class="badge">{h_score} pts</span>' if h_score else ''
    source_html = f'<span class="src">{html.escape(h_source)}</span>' if h_source else ''

    # Highlight block
    cards = f'''<section class="highlight">
<div class="meta">{source_html}{score_html}</div>
<h3>🔥 {h_title}</h3>
'''
    if h_url:
        cards += f'<p class="link"><a href="{html.escape(h_url)}" target="_blank">📎 Source →</a></p>'
    cards += '</section>'

    # Related topics
    if related:
        cards += '<section class="related"><h2>📌 Also trending</h2><ul>'
        for item in related:
            title = html.escape(item.get("title", ""))
            pts = item.get("points") or item.get("ups", "")
            url = item.get("url", "")
            li = f'<li>{title}'
            if pts:
                li += f' <span class="badge">{pts} pts</span>'
            if url:
                li += f' <a href="{html.escape(url)}" target="_blank">📎</a>'
            li += '</li>'
            cards += li
        cards += '</ul></section>'

    mock = data.get("mock_post") or {}
    if mock.get("text"):
        cards += mock_post_card(mock, date_str)

    summaries = data.get("summaries") or []
    if summaries:
        cards += '<section class="summaries"><h2>🧠 Article summaries</h2>'
        for row in summaries:
            title = html.escape(row.get("title", ""))
            summary = html.escape(row.get("summary", ""))
            url = row.get("url", "")
            if not title or not summary:
                continue
            cards += f'<article class="summary"><h3>{title}</h3><p>{summary}</p>'
            if url:
                cards += f'<p class="link"><a href="{html.escape(url)}" target="_blank">Read →</a></p>'
            cards += '</article>'
        cards += '</section>'

    # X refs
    if x_refs:
        cards += '<section class="x-refs"><h2>🐦 On X</h2>'
        for topic, tweets in list(x_refs.items())[:3]:
            cards += f'<details><summary>{html.escape(topic[:60])}</summary><ul>'
            for tw in tweets:
                cards += f'<li><a href="{html.escape(tw.get("url", "#"))}" target="_blank">Tweet →</a></li>'
            cards += '</ul></details>'
        cards += '</section>'

    return cards


def mock_post_card(mock: dict, day: str = "") -> str:
    """X-style mock post so the summarization is copy-ready."""
    handle = html.escape(mock.get("handle") or "Trend Threads")
    username = html.escape(mock.get("username") or "trendthreads")
    body = html.escape(mock.get("text") or "")
    short = html.escape(mock.get("short") or "")
    chars = mock.get("chars") or len(mock.get("text") or "")
    short_chars = mock.get("short_chars") or len(mock.get("short") or "")
    stamp = html.escape(day or "")
    short_html = ""
    if short:
        short_html = (
            f'<details class="short-hook"><summary>280-char hook · {short_chars} chars</summary>'
            f'<p class="mock-body">{short}</p></details>'
        )
    return f'''<section class="mock-wrap">
<p class="mock-badge">Mock post · not posted</p>
<article class="mock-post">
<div class="mock-head">
<div class="avatar" aria-hidden="true">📡</div>
<div>
<div class="mock-name">{handle}</div>
<div class="mock-user">@{username}{f" · {stamp}" if stamp else ""}</div>
</div>
</div>
<p class="mock-body">{body}</p>
<div class="mock-meta"><span>{chars} chars</span><span>💬  🔁  ❤️  🔖</span></div>
</article>
{short_html}
</section>'''


def collect_topics(raw) -> list:
    if isinstance(raw, dict):
        if isinstance(raw.get("trends"), dict):
            raw = raw["trends"]
        elif isinstance(raw.get("trends"), list):
            return raw["trends"]
    if isinstance(raw, dict):
        topics = []
        for v in raw.values():
            if isinstance(v, list):
                topics.extend(v)
        return topics
    return raw if isinstance(raw, list) else []


def page(day: str, icumi_data: dict) -> str:
    """Generate full HTML page from ICUMI data."""
    cards = icumi_card(icumi_data)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trend Threads — {day}</title>
<style>
:root{{color-scheme:dark}}body{{background:#0b1220;color:#e8eef7;font:16px/1.55 system-ui,sans-serif;margin:0 auto;max-width:640px;padding:24px 16px}}
h1{{font-size:22px}}h2{{font-size:15px;color:#8fa1b8;text-transform:uppercase;letter-spacing:.08em}}
.highlight{{background:#101b30;border:1px solid #1e2c47;border-radius:12px;padding:16px;margin:12px 0}}
.highlight h3{{margin:4px 0 8px}}
.related{{margin:12px 0}}.related ul{{padding-left:18px}}
.summaries{{margin:16px 0}}.summary{{background:#101b30;border:1px solid #1e2c47;border-radius:12px;padding:14px;margin:10px 0}}
.summary h3{{margin:0 0 8px;font-size:16px}}
.summary p{{margin:0 0 8px;color:#c5d0e0}}
.mock-wrap{{margin:18px 0}}
.mock-badge{{display:inline-block;background:#1e2c47;color:#ffc156;font-size:11px;padding:2px 8px;border-radius:999px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px}}
.mock-post{{background:#101b30;border:1px solid #1e2c47;border-radius:16px;padding:16px}}
.mock-head{{display:flex;gap:12px;align-items:center}}
.avatar{{width:44px;height:44px;border-radius:50%;background:#1e2c47;display:grid;place-items:center;font-size:22px}}
.mock-name{{font-weight:700}}
.mock-user{{color:#8fa1b8;font-size:13px}}
.mock-body{{white-space:pre-wrap;margin:12px 0 8px;font-size:17px;line-height:1.45}}
.mock-meta{{display:flex;justify-content:space-between;color:#8fa1b8;font-size:12px;border-top:1px solid #1e2c47;padding-top:10px}}
.short-hook{{margin-top:10px;padding:8px;background:#101b30;border:1px solid #1e2c47;border-radius:8px}}
.short-hook summary{{cursor:pointer;color:#8fa1b8}}
.x-refs{{margin:12px 0}}.x-refs details{{margin:6px 0;padding:8px;background:#101b30;border-radius:8px;border:1px solid #1e2c47}}
.x-refs details summary{{cursor:pointer;font-weight:600}}
.x-refs details ul{{margin:8px 0 0;padding-left:18px}}
.badge{{background:#1e2c47;color:#4adee6;padding:2px 8px;border-radius:10px;font-size:12px;margin-left:6px}}
.src{{color:#ffc156;font-size:12px}}.link{{margin:4px 0}}
.meta{{display:flex;justify-content:space-between;font-size:12px;color:#7d8ea8;margin-bottom:6px}}
footer{{color:#5c6b84;font-size:12px;margin-top:28px}}a{{color:#4adee6;text-decoration:none}}a:hover{{text-decoration:underline}}
</style></head><body>
<h1>📡 Trend Threads — {day}</h1>
<h2>In Case You Missed It</h2>
{cards}
<footer>Generated by Hermes Studio · <a href="../">archive</a></footer>
</body></html>
"""


def archive_index(days: list) -> None:
    links = "".join(f'<li><a href="{d}/">{d}</a></li>' for d in sorted(days, reverse=True))
    (OUT / "index.html").write_text(
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Trend Threads archive</title></head><body style='background:#0b1220;"
        f"color:#e8eef7;font:16px system-ui;max-width:640px;margin:0 auto;padding:24px 16px'>"
        f"<h1>📡 Trend Threads</h1><ul>{links}</ul></body></html>"
    )


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        print(f"bad date: {day} (want YYYY-MM-DD)")
        return 2
    ddir = ROOT / "data" / day
    icumi_f = ddir / "icumi.json"
    icumi_data = {}
    if icumi_f.exists():
        try:
            icumi_data = json.loads(icumi_f.read_text())
        except json.JSONDecodeError:
            pass
    outdir = OUT / day
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(page(day, icumi_data))
    days = [p.name for p in OUT.iterdir()
            if p.is_dir() and (p / "index.html").exists()]
    archive_index(days)
    h = icumi_data.get("highlight", {})
    print(f"rendered {day}: '{h.get('title', 'none')[:50]}' + {len(icumi_data.get('related', []))} related → docs/{day}/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
