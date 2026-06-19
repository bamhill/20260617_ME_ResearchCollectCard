"""Tests for RssFetcher."""

from datetime import date
from unittest.mock import patch, MagicMock
from src.fetchers.rss import RssFetcher
from src.models import Source, SourceType


def test_fetch_parses_entries():
    fetcher = RssFetcher()
    source = Source(id="test_rss", name="Test", type=SourceType.RSS,
                    query="https://example.com/feed")

    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [
        {
            "title": "Test Article",
            "link": "https://mp.weixin.qq.com/s/test",
            "summary": "<p>Test content</p>",
            "author": "Test Author",
            "published_parsed": (2026, 6, 17, 10, 0, 0, 1, 168, 0),
        }
    ]

    with patch("src.fetchers.rss.feedparser.parse", return_value=mock_feed):
        items = fetcher.fetch(source, date(2026, 6, 17))

    assert len(items) == 1
    item = items[0]
    assert item.title == "Test Article"
    assert item.url == "https://mp.weixin.qq.com/s/test"
    assert item.summary_raw == "Test content"
    assert item.source_id == "test_rss"


def test_fetch_bozo_feed_with_entries():
    """Bozo feed with entries should still return results."""
    fetcher = RssFetcher()
    source = Source(id="test_rss", name="Test", type=SourceType.RSS,
                    query="https://example.com/feed")

    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.entries = [
        {
            "title": "Bozo Article",
            "link": "https://example.com",
            "summary": "",
            "published_parsed": (2026, 6, 17, 10, 0, 0, 1, 168, 0),
        }
    ]

    with patch("src.fetchers.rss.feedparser.parse", return_value=mock_feed):
        items = fetcher.fetch(source, date(2026, 6, 17))

    assert len(items) == 1


def test_fetch_empty_when_bozo_and_no_entries():
    fetcher = RssFetcher()
    source = Source(id="test_rss", name="Test", type=SourceType.RSS,
                    query="https://example.com/feed")

    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.entries = []

    with patch("src.fetchers.rss.feedparser.parse", return_value=mock_feed):
        items = fetcher.fetch(source, date(2026, 6, 17))

    assert items == []
