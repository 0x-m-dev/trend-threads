"""Tests for Trend Threads — scrape, draft, deliver."""

import json
import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import sys
import os

import scrape
import draft


# ---------------------------------------------------------------------------
# Scrape tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Scrape tests (mocked — no network)
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


class TestDraft:
    """Test thread drafting."""

    def test_cluster_topics(self):
        sample_trends = [
            {"title": "OpenAI launches new agent platform", "source": "TechCrunch", "score": 50},
            {"title": "AI agents are transforming software development", "source": "Hacker News", "score": 120},
            {"title": "OpenAI confirms new security framework", "source": "The Verge", "score": 30},
            {"title": "Python 3.13 released with new features", "source": "TechCrunch", "score": 80},
        ]
        clusters = draft.cluster_topics(sample_trends, max_clusters=3)
        assert len(clusters) <= 3
        for cluster in clusters:
            assert len(cluster) >= 1

    def test_draft_thread_output(self):
        sample_trends = [
            {"title": "OpenAI launches new AI agent platform", "source": "TechCrunch", "score": 200},
            {"title": "AI agents transform software development", "source": "Hacker News", "score": 150},
            {"title": "UK government bans AI in schools", "source": "BBC Top News", "score": 0},
            {"title": "German rocket reaches orbit successfully", "source": "BBC Top News", "score": 0},
            {"title": "Python 3.13 now available", "source": "TechCrunch", "score": 0},
        ]
        clusters = draft.cluster_topics(sample_trends, max_clusters=4)
        thread = draft.draft_thread(clusters)

        assert "🧵" in thread
        assert "/7)" in thread  # Has tweet numbering
        assert "👇" in thread  # Has CTA


class TestDeliver:
    """Test Discord delivery message."""

    def test_deliver_message_format(self, tmp_path: Path):
        """deliver.py produces a message with required elements."""
        # Create mock data
        data_dir = tmp_path / "data" / date.today().isoformat()
        data_dir.mkdir(parents=True)

        trends = {
            "date": date.today().isoformat(),
            "total_trends": 50,
            "source_counts": {"Hacker News": 20, "BBC": 15, "TechCrunch": 15},
            "trends": [{"title": "Test", "source": "Test"}],
        }
        (data_dir / "trends.json").write_text(json.dumps(trends))

        thread_text = "🧵 This is a test thread\n\n(1/5)"
        (data_dir / "thread.md").write_text(thread_text)

        # Mock the OUTPUT_DIR in deliver.py
        import deliver
        original_dir = deliver.OUTPUT_DIR
        deliver.OUTPUT_DIR = data_dir

        try:
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                deliver.main()
            output = f.getvalue()

            assert "Trend Threads" in output
            assert date.today().strftime('%B %d, %Y') in output
            assert "scraped" in output.lower()
            assert "🧵" in output
            assert "thread.md" in output
        finally:
            deliver.OUTPUT_DIR = original_dir


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
