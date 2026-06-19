"""Tests for ArxivFetcher."""

from datetime import date
from src.fetchers.arxiv import ArxivFetcher
from src.models import Source, SourceType

ARXIV_ATOM_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2306.00001</id>
    <title>Test Paper Title</title>
    <summary>  This is a test abstract.  </summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <published>2026-06-17T12:00:00Z</published>
  </entry>
</feed>"""


def test_parse_atom():
    fetcher = ArxivFetcher()
    source = Source(id="test", name="Test", type=SourceType.ARXIV, query="cat:cs.CL")
    items = fetcher._parse_atom(ARXIV_ATOM_RESPONSE, source.id, date(2026, 6, 17))

    assert len(items) == 1
    item = items[0]
    assert item.title == "Test Paper Title"
    assert item.authors == ["Alice", "Bob"]
    assert item.url == "http://arxiv.org/abs/2306.00001"
    assert item.summary_raw == "This is a test abstract."
    assert item.published == date(2026, 6, 17)


def test_parse_atom_empty():
    fetcher = ArxivFetcher()
    source = Source(id="test", name="Test", type=SourceType.ARXIV, query="cat:cs.CL")
    items = fetcher._parse_atom("<feed></feed>", source.id, date(2026, 6, 17))
    assert items == []
