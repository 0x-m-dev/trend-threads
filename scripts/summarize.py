#!/usr/bin/env python3
"""Fetch article excerpts and build a copy-ready mock X post.

Stdlib only. Network failures fall back to the article title.
"""
from __future__ import annotations

import html
import re
import urllib.request
from datetime import date

UA = {"User-Agent": "trend-threads/1.0 (hermes-studio)"}
SHORT_LIMIT = 280
SUMMARY_LIMIT = 220

_SKIP_PREFIXES = (
    "skip to",
    "cookie",
    "subscribe",
    "sign in",
    "log in",
    "javascript is disabled",
    "share this",
    "follow us",
)


def strip_tags(raw: str) -> str:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", text)
    text = re.sub(r"(?is)<nav[^>]*>.*?</nav>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def meta_description(raw: str) -> str:
    patterns = [
        r'<meta[^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, raw, re.I)
        if m:
            desc = html.unescape(m.group(1)).strip()
            if len(desc) >= 40:
                return desc
    return ""


def first_sentences(text: str, limit: int = SUMMARY_LIMIT) -> str:
    kept = []
    for line in text.splitlines():
        low = line.lower().strip()
        if not low:
            continue
        if any(low.startswith(p) for p in _SKIP_PREFIXES):
            continue
        kept.append(line.strip())
    cleaned = re.sub(r"\s+", " ", " ".join(kept)).strip()
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    picked: list[str] = []
    for sent in parts:
        low = sent.lower().strip()
        if len(low) < 40:
            continue
        if any(low.startswith(p) for p in _SKIP_PREFIXES):
            continue
        picked.append(sent.strip())
        blob = " ".join(picked)
        if len(blob) >= 90 or len(picked) >= 2:
            break
    blob = " ".join(picked) if picked else cleaned
    if len(blob) > limit:
        blob = blob[: limit - 1].rsplit(" ", 1)[0] + "…"
    return blob


def extract_summary(raw_html: str, title: str = "", limit: int = SUMMARY_LIMIT) -> str:
    desc = meta_description(raw_html)
    if desc:
        return first_sentences(desc, limit=limit) or desc[:limit]
    body = strip_tags(raw_html)
    summary = first_sentences(body, limit=limit)
    return summary or (title or "")[:limit]


def fetch_html(url: str, timeout: int = 12) -> str:
    if not url or not url.startswith("http"):
        return ""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read(180_000).decode(charset, errors="replace")


def summarize_item(item: dict, timeout: int = 12) -> dict:
    title = (item.get("title") or "").strip()
    url = (item.get("url") or "").strip()
    summary = ""
    try:
        raw = fetch_html(url, timeout=timeout)
        if raw:
            summary = extract_summary(raw, title=title)
    except Exception:
        summary = ""
    if not summary:
        summary = title
    return {
        "title": title,
        "url": url,
        "summary": summary,
        "score": item.get("score") or item.get("points") or item.get("ups") or 0,
        "source": item.get("source", ""),
    }


def summarize_items(items: list[dict], timeout: int = 12) -> list[dict]:
    return [summarize_item(item, timeout=timeout) for item in items]


def clamp_tweet(text: str, limit: int = SHORT_LIMIT) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def _one_liner(entry: dict) -> str:
    return (entry.get("summary") or entry.get("title") or "").strip()


def build_mock_post(
    highlight: dict,
    related: list[dict],
    summaries: list[dict] | None = None,
    day: date | None = None,
) -> dict:
    """Build long + short copy-ready X posts from article summaries."""
    day = day or date.today()
    stamp = f"{day.strftime('%b')} {day.day}"

    by_title = {}
    for row in summaries or []:
        title = (row.get("title") or "").strip()
        if title:
            by_title[title] = row

    def resolved(item: dict) -> dict:
        title = (item.get("title") or "").strip()
        found = by_title.get(title, {})
        return {
            "title": title,
            "url": item.get("url") or found.get("url", ""),
            "summary": found.get("summary") or title,
            "score": item.get("score") or found.get("score") or 0,
        }

    h = resolved(highlight) if highlight else {}
    rel = [resolved(r) for r in related]

    h_line = _one_liner(h) if h else "No highlight today."
    score = h.get("score") or 0
    score_bit = f" ({score} pts)" if score else ""

    long_lines = [
        f"ICYMI — {stamp}",
        "",
        f"🔥 {h_line}{score_bit}",
    ]
    if rel:
        long_lines.append("")
        long_lines.append("Also:")
        for item in rel:
            long_lines.append(f"• {_one_liner(item)}")
        long_lines.append("")
        long_lines.append("Which one did you actually miss?")
    long_text = "\n".join(long_lines).strip()

    also = "; ".join(_one_liner(item) for item in rel[:4])
    short = f"ICYMI: {h_line}"
    if also:
        short = f"{short} Also: {also}"
    short = clamp_tweet(short)

    return {
        "handle": "Trend Threads",
        "username": "trendthreads",
        "text": long_text,
        "short": short,
        "chars": len(long_text),
        "short_chars": len(short),
    }
