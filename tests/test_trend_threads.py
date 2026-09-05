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

class TestScrapeRSS:
    """Test RSS feed fetching."""

    def test_hn_rss_parsing(self):
        items = scrape.fetch_rss_feed("Hacker News", "https://hnrss.org/frontpage")
        assert len(items) >= 5, f"Expected ≥5 HN items, got {len(items)}"
        for item in items:
            assert "title" in item
            assert "source" in item
            assert item["source"] == "Hacker News"
            assert len(item["title"]) >= 10

    def test_bbc_rss_parsing(self):
        items = scrape.fetch_rss_feed("BBC", "http://feeds.bbci.co.uk/news/rss.xml")
        assert len(items) >= 5, f"Expected ≥5 BBC items, got {len(items)}"
        for item in items:
            assert len(item["title"]) >= 10

    def test_techcrunch_rss_parsing(self):
        items = scrape.fetch_rss_feed("TechCrunch", "https://techcrunch.com/feed/")
        assert len(items) >= 5, f"Expected ≥5 TechCrunch items, got {len(items)}"
        for item in items:
            assert item["source"] == "TechCrunch"


class TestScrapeHN:
    """Test Hacker News top stories."""

    def test_hn_fetch(self):
        items = scrape.fetch_hn_top()
        assert isinstance(items, list)
        for item in items:
            assert "title" in item
            assert item["source"] == "Hacker News"
            assert "score" in item
            assert item["score"] >= scrape.HN_MIN_SCORE


class TestScrapeCombined:
    """Test full scrape output."""

    def test_output_format(self, tmp_path: Path):
        """scrape() returns correct dict structure."""
        orig_dir = Path(__file__).parent.parent / "data" / date.today().isoformat()
        # Temporarily override OUTPUT_DIR for test
        original_output = scrape.OUTPUT_DIR
        scrape.OUTPUT_DIR = tmp_path / "test"

        try:
            result = scrape.scrape()
            assert "date" in result
            assert "sources" in result
            assert "source_counts" in result
            assert "total_trends" in result
            assert "trends" in result
            assert isinstance(result["trends"], list)
            assert result["total_trends"] >= 10
            assert len(result["sources"]) >= 2
        finally:
            scrape.OUTPUT_DIR = original_output


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
