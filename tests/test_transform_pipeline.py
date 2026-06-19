"""Tests for TransformPipeline."""

from datetime import date
from src.pipeline.transform import TransformPipeline
from src.models import Card, CardType, PaperItem


def test_dedup_by_url():
    items = [
        PaperItem(title="A", url="https://a.com", source_id="s1"),
        PaperItem(title="A Duplicate", url="https://a.com", source_id="s1"),
        PaperItem(title="B", url="https://b.com", source_id="s1"),
    ]
    card = Card(id="paper_20260617", type=CardType.PAPER, date=date(2026, 6, 17), items=items)
    pipeline = TransformPipeline()
    result = pipeline.run([card])
    assert result[0].item_count == 2


def test_sort_by_date_desc():
    items = [
        PaperItem(title="Old", url="https://old.com", source_id="s1",
                   published=date(2026, 6, 15)),
        PaperItem(title="New", url="https://new.com", source_id="s1",
                   published=date(2026, 6, 17)),
    ]
    card = Card(id="paper_20260617", type=CardType.PAPER, date=date(2026, 6, 17), items=items)
    pipeline = TransformPipeline()
    result = pipeline.run([card])
    assert result[0].items[0].title == "New"
    assert result[0].items[1].title == "Old"
