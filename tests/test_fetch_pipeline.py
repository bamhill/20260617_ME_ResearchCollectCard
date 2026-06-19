"""Tests for FetchPipeline."""

from datetime import date
from unittest.mock import MagicMock
from src.pipeline.fetch import FetchPipeline
from src.models import Source, SourceType, PaperItem, DateRange


def test_fetch_pipeline_single_day():
    mock_fetcher = MagicMock()
    mock_fetcher.source_type = "arxiv"
    mock_fetcher.fetch.return_value = [
        PaperItem(title="Paper 1", url="https://arxiv.org/abs/0001", source_id="test_arxiv")
    ]

    pipeline = FetchPipeline({"arxiv": mock_fetcher})
    sources = [Source(id="test_arxiv", name="Test", type=SourceType.ARXIV, query="cat:cs.CL")]
    dr = DateRange.single(date(2026, 6, 17))

    cards = pipeline.run("paper", sources, dr)

    assert len(cards) == 1
    assert cards[0].id == "paper_20260617"
    assert cards[0].item_count == 1
    mock_fetcher.fetch.assert_called_once()


def test_fetch_pipeline_date_range():
    mock_fetcher = MagicMock()
    mock_fetcher.source_type = "arxiv"
    mock_fetcher.fetch.return_value = []

    pipeline = FetchPipeline({"arxiv": mock_fetcher})
    sources = [Source(id="test_arxiv", name="Test", type=SourceType.ARXIV, query="cat:cs.CL")]
    dr = DateRange(start=date(2026, 6, 15), end=date(2026, 6, 17))

    cards = pipeline.run("paper", sources, dr)

    assert len(cards) == 3
    assert mock_fetcher.fetch.call_count == 3
