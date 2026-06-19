"""Tests for Pydantic models."""

from datetime import date, datetime
import pytest
from src.models import Source, SourceType, Card, CardType, CardMeta, PaperItem, WechatItem, RawItem, DateRange


class TestSource:
    def test_source_creation_minimal(self):
        s = Source(id="test", name="Test", type=SourceType.RSS)
        assert s.id == "test"
        assert s.tags == []

    def test_source_serialization(self):
        s = Source(id="arxiv_cs_cl", name="arXiv CS.CL", type=SourceType.ARXIV,
                   query="cat:cs.CL", tags=["NLP", "LLM"])
        data = s.model_dump()
        roundtrip = Source.model_validate(data)
        assert roundtrip == s


class TestDateRange:
    def test_single_date(self):
        dr = DateRange.single(date(2026, 6, 17))
        assert dr.start == dr.end == date(2026, 6, 17)

    def test_dates_generation(self):
        dr = DateRange(start=date(2026, 6, 15), end=date(2026, 6, 17))
        dates = dr.dates()
        assert len(dates) == 3
        assert dates[0] == date(2026, 6, 15)
        assert dates[-1] == date(2026, 6, 17)


class TestCard:
    def test_card_creation(self):
        card = Card(
            id="paper_20260617",
            type=CardType.PAPER,
            date=date(2026, 6, 17),
            items=[
                PaperItem(
                    title="Test Paper",
                    url="https://arxiv.org/abs/2306.00001",
                    source_id="arxiv_cs_cl",
                    paper_id="2306.00001",
                )
            ],
        )
        assert card.item_count == 1
        meta = card.to_meta()
        assert meta.type == CardType.PAPER
        assert meta.item_count == 1

    def test_idea_count(self):
        card = Card(
            id="paper_20260617",
            type=CardType.PAPER,
            date=date(2026, 6, 17),
            items=[
                PaperItem(title="Idea Paper", url="https://a.com", source_id="s1", is_idea=True),
                PaperItem(title="Normal Paper", url="https://b.com", source_id="s1", is_idea=False),
            ],
        )
        assert card.idea_count == 1
        assert card.to_meta().idea_count == 1

    def test_card_serialization_roundtrip(self):
        card = Card(
            id="paper_20260617",
            type=CardType.PAPER,
            date=date(2026, 6, 17),
            items=[
                PaperItem(title="T", url="https://x.com", source_id="s1", paper_id="2306.00001"),
            ],
        )
        data = card.model_dump()
        restored = Card.model_validate(data)
        assert restored == card
        assert restored.items[0].paper_id == "2306.00001"

    def test_empty_card(self):
        card = Card(id="empty", type=CardType.WECHAT, date=date(2026, 6, 17))
        assert card.item_count == 0
        assert card.idea_count == 0


class TestItemFields:
    def test_paper_item_fields(self):
        item = PaperItem(
            title="Test Paper",
            url="https://arxiv.org/abs/2306.00001",
            source_id="s1",
            paper_id="2306.00001",
            summary_zh="中文摘要",
        )
        assert item.paper_id == "2306.00001"
        assert item.summary_zh == "中文摘要"
        assert item.is_idea is False

    def test_wechat_item_fields(self):
        item = WechatItem(
            title="Test Article",
            url="https://mp.weixin.qq.com/s/abc",
            source_id="s1",
            mp_url="https://mp.weixin.qq.com/s/abc",
            summary_zh="中文摘要",
        )
        assert item.mp_url == "https://mp.weixin.qq.com/s/abc"
        assert item.summary_zh == "中文摘要"

    def test_raw_item_is_idea_default(self):
        item = RawItem(title="T", url="https://x.com", source_id="s1")
        assert item.is_idea is False
        item.is_idea = True
        assert item.is_idea is True
