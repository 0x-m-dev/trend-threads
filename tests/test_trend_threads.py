"""Tests for Trend Threads — scrape, draft, deliver (ICUMI format)."""

import json
import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scrape
import draft
import deliver


# ---------------------------------------------------------------------------
# Scrape tests
# ---------------------------------------------------------------------------
from unittest.mock import patch


def _reddit_payload():
    return {"data": {"children": [
        {"data": {"title": f"Post {i}", "permalink": f"/r/x/comments/{i}",
                  "ups": 100 + i, "num_comments": 10 + i}} for i in range(3)]}}


class TestFetchReddit:
    def test_shape(self):
        with patch.object(scrape, "get_json", return_value=_reddit_payload()):
            items = scrape.fetch_reddit()
        assert len(items) == 3
        for it in items:
            assert {"source", "title", "url"} <= set(it)
            assert it["source"] == "reddit"
            assert it["title"] == it["title"].strip() and it["title"]


class TestFetchHN:
    def test_shape(self):
        def fake(url, timeout=15):
            if url == scrape.SOURCES["hackernews_ids"]:
                return [11, 22]
            return {"title": "HN story", "url": "https://x.test", "score": 42}
        with patch.object(scrape, "get_json", side_effect=fake):
            items = scrape.fetch_hn()
        assert len(items) == 2
        assert all(it["source"] == "hacker_news" and it["title"] for it in items)


RSS_SAMPLE = """<?xml version="1.0"?><rss><channel>
<item><title>Alpha news story here</title><link>https://x.test/a</link></item>
<item><title>Beta news story here</title><link>https://x.test/b</link></item>
</channel></rss>"""


class TestFetchRSS:
    def test_parses_items(self):
        class Resp:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self):
                return RSS_SAMPLE.encode()
        with patch.object(scrape.urllib.request, "urlopen", return_value=Resp()):
            items = scrape.fetch_rss()
        assert len(items) >= 2
        assert all(it["source"] == "news" and it["title"] for it in items)


# ---------------------------------------------------------------------------
# Summarize + mock post tests
# ---------------------------------------------------------------------------

OG_HTML = """<html><head>
<meta property="og:description" content="Isar Aerospace became the first commercial space company from Europe to deliver satellites into orbit on its second flight.">
</head><body><p>Skip to content</p><p>Cookie banner goes here for everyone visiting the site today.</p></body></html>"""

BODY_HTML = """<html><body>
<nav>Home About Contact</nav>
<p>Skip to main content</p>
<p>NetBSD 9.5 is the fifth and final release from the NetBSD 9 stable branch.</p>
<p>This also marks the end-of-support for all NetBSD-9.x releases.</p>
</body></html>"""


class TestSummarize:
    def test_extract_prefers_og_description(self):
        import summarize
        summary = summarize.extract_summary(OG_HTML, title="Ignored title")
        assert "first commercial space company" in summary
        assert "Ignored title" not in summary

    def test_extract_falls_back_to_body(self):
        import summarize
        summary = summarize.extract_summary(BODY_HTML, title="NetBSD 9.5")
        assert "final release" in summary

    def test_clamp_tweet_limit(self):
        import summarize
        long = "word " * 80
        out = summarize.clamp_tweet(long, limit=50)
        assert len(out) <= 50
        assert out.endswith("…")

    def test_build_mock_post(self):
        import summarize
        from datetime import date as d
        highlight = {"title": "qBit joke", "score": 1042}
        related = [{"title": "Orbit"}, {"title": "Fly"}]
        summaries = [
            {"title": "qBit joke", "summary": "A sandbox-escape bit about torrents."},
            {"title": "Orbit", "summary": "A European rocket reached orbit."},
            {"title": "Fly", "summary": "LLM-written posts are obvious."},
        ]
        mock = summarize.build_mock_post(highlight, related, summaries, day=d(2026, 9, 6))
        assert mock["text"].startswith("ICYMI — Sep 6")
        assert "sandbox-escape" in mock["text"]
        assert "European rocket" in mock["text"]
        assert mock["short_chars"] <= 280
        assert mock["chars"] == len(mock["text"])


# ---------------------------------------------------------------------------
# Draft tests (ICUMI format)
# ---------------------------------------------------------------------------


class TestDraft:
    """Test ICUMI-style drafting."""

    def test_flatten_trends(self):
        data = {
            "reddit": [{"title": "Reddit post", "ups": 100, "url": "https://r.test/1"}],
            "hacker_news": [{"title": "HN story", "points": 50, "url": "https://hn.test/1"}],
        }
        flat = draft.flatten_trends(data)
        assert len(flat) == 2
        scores = [t.get("score", 0) for t in flat]
        assert scores == sorted(scores, reverse=True)  # Sorted by score desc

    def test_pick_highlight(self):
        trends = [
            {"title": "Top story", "score": 1000, "url": "https://t.test", "source": "hn"},
            {"title": "Second", "score": 500, "url": "https://s.test", "source": "hn"},
        ]
        h = draft.pick_highlight(trends)
        assert h["title"] == "Top story"
        assert h["score"] == 1000

    def test_pick_related(self):
        trends = [
            {"title": "AI agents transform coding", "score": 1000, "url": "https://t.test", "source": "hn"},
            {"title": "Rocket reaches orbit successfully", "score": 500, "url": "https://r.test", "source": "hn"},
            {"title": "New Python release today", "score": 300, "url": "https://p.test", "source": "hn"},
        ]
        related = draft.pick_related(trends, count=2)
        assert len(related) == 2
        titles = [t["title"] for t in related]
        assert "AI agents transform coding" not in titles  # Not in related

    def test_extract_keywords(self):
        kw = draft.extract_keywords("QBittorrent breaks out of sandbox to commit crimes")
        assert len(kw) > 0
        assert all(len(w) >= 3 for w in kw)

    def test_icumi_text_format(self):
        highlight = {"title": "Test story", "score": 999, "url": "https://t.test", "source": "hn"}
        related = [{"title": "Related 1", "score": 100, "url": "https://r.test", "source": "hn"}]
        x_refs = {}
        text = draft.build_icumi(highlight, related, x_refs)
        assert "📡 In Case You Missed It" in text
        assert "**Test story" in text  # Bold title
        assert "999 pts" in text
        assert "Related 1" in text
        assert "🔗 Full archive" in text

    def test_icumi_json_format(self):
        highlight = {"title": "Test", "score": 50, "url": "https://t.test", "source": "hn"}
        related = [{"title": "R", "score": 10, "url": "https://r.test", "source": "hn"}]
        mock = {"text": "ICYMI — Test", "short": "ICYMI: Test", "chars": 12}
        summaries = [{"title": "Test", "summary": "A short recap.", "url": "https://t.test"}]
        data = draft.build_icumi_json(highlight, related, {}, mock_post=mock, summaries=summaries)
        assert data["highlight"]["title"] == "Test"
        assert len(data["related"]) == 1
        assert data["total_trends"] == 2
        assert data["mock_post"]["text"].startswith("ICYMI")
        assert data["summaries"][0]["summary"] == "A short recap."

    def test_icumi_includes_mock_post(self):
        highlight = {"title": "Test story", "score": 999, "url": "https://t.test", "source": "hn"}
        related = [{"title": "Related 1", "score": 100, "url": "https://r.test", "source": "hn"}]
        mock = {"text": "ICYMI — a recap of Test story", "short": "ICYMI: Test story", "short_chars": 17}
        text = draft.build_icumi(highlight, related, {}, mock_post=mock)
        assert "Mock post" in text
        assert "ICYMI — a recap of Test story" in text

    def test_normalize_title(self):
        t = draft.normalize_title("Test — story with  &#8217; quotes")
        assert "—" not in t
        assert "'" in t


# ---------------------------------------------------------------------------
# Deliver tests (ICUMI format)
# ---------------------------------------------------------------------------

class TestDeliver:
    """Test Discord ICUMI delivery."""

    def test_deliver_message_format(self, tmp_path: Path):
        """deliver.py produces an ICUMI message with required elements."""
        data_dir = tmp_path / "data" / date.today().isoformat()
        data_dir.mkdir(parents=True)

        icumi_data = {
            "date": date.today().isoformat(),
            "highlight": {"title": "Trend Threads test", "score": 50, "url": "https://t.test", "source": "hn"},
            "related": [{"title": "R1", "score": 10, "url": "https://r.test", "source": "hn"}],
            "x_refs": {},
            "total_trends": 2,
        }
        (data_dir / "icumi.json").write_text(json.dumps(icumi_data))
        (data_dir / "icumi.md").write_text(
            f"📡 In Case You Missed It\n📅 {date.today().strftime('%B %d, %Y')}\n\n"
            f"🔥 **Trend Threads test (50 pts)**\n"
            f"📊 Sources: HN"
        )

        import deliver
        original_dir = deliver.OUTPUT_DIR
        original_icumi_file = deliver.ICUMI_FILE
        original_text_file = deliver.ICUMI_TEXT_FILE
        deliver.OUTPUT_DIR = data_dir
        deliver.ICUMI_FILE = data_dir / "icumi.json"
        deliver.ICUMI_TEXT_FILE = data_dir / "icumi.md"

        try:
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                deliver.main()
            output = f.getvalue()

            assert "Trend Threads" in output
            assert date.today().strftime('%B %d, %Y') in output
            assert "📡 In Case You Missed It" in output
            assert "🔥" in output
        finally:
            deliver.OUTPUT_DIR = original_dir
            deliver.ICUMI_FILE = original_icumi_file
            deliver.ICUMI_TEXT_FILE = original_text_file


# ---------------------------------------------------------------------------
# Render tests
# ---------------------------------------------------------------------------

class TestRender:
    """Test HTML rendering."""

    def test_icumi_card(self):
        data = {
            "highlight": {"title": "Test", "score": 100, "url": "https://t.test", "source": "hn"},
            "related": [{"title": "R", "score": 50, "url": "https://r.test", "source": "hn"}],
            "x_refs": {},
        }
        from scripts.render import icumi_card
        card = icumi_card(data)
        assert "Test" in card
        assert "100 pts" in card
        assert "R" in card
        assert "https://t.test" in card

    def test_icumi_card_no_highlight(self):
        from scripts.render import icumi_card
        card = icumi_card({})
        assert "No data" in card

    def test_page_generates_valid_html(self):
        from scripts.render import page
        data = {
            "highlight": {"title": "Test", "score": 100, "url": "https://t.test", "source": "hn"},
            "related": [],
            "x_refs": {},
        }
        html = page("2026-09-06", data)
        assert "<!doctype html>" in html
        assert "Trend Threads" in html
        assert "Test" in html

    def test_mock_post_card(self):
        from scripts.render import icumi_card
        data = {
            "highlight": {"title": "Test", "score": 100, "url": "https://t.test", "source": "hn"},
            "related": [],
            "x_refs": {},
            "summaries": [{"title": "Test", "summary": "Something actually happened.", "url": "https://t.test"}],
            "mock_post": {
                "handle": "Trend Threads",
                "username": "trendthreads",
                "text": "ICYMI — Something actually happened.",
                "short": "ICYMI: Something actually happened.",
                "chars": 36,
                "short_chars": 35,
            },
        }
        card = icumi_card(data)
        assert "mock-post" in card
        assert "Something actually happened." in card
        assert "Article summaries" in card
        assert "@trendthreads" in card


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
