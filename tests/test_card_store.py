"""Tests for CardRepository."""

import tempfile
from datetime import date
from pathlib import Path
from src.store.card_store import CardRepository
from src.models import Card, CardType, PaperItem


def test_save_and_load():
    with tempfile.TemporaryDirectory() as tmp:
        repo = CardRepository(Path(tmp))
        card = Card(
            id="paper_20260617",
            type=CardType.PAPER,
            date=date(2026, 6, 17),
            items=[
                PaperItem(
                    title="A Test Paper",
                    url="https://example.com",
                    source_id="test",
                )
            ],
        )
        path = repo.save(card)
        assert path.exists()
        assert path.suffix == ".json"

        loaded = repo.load("paper", date(2026, 6, 17))
        assert loaded is not None
        assert loaded.id == "paper_20260617"
        assert loaded.item_count == 1


def test_list_all():
    with tempfile.TemporaryDirectory() as tmp:
        repo = CardRepository(Path(tmp))
        card1 = Card(id="paper_20260616", type=CardType.PAPER,
                      date=date(2026, 6, 16), items=[])
        card2 = Card(id="paper_20260617", type=CardType.PAPER,
                      date=date(2026, 6, 17), items=[])
        repo.save(card1)
        repo.save(card2)

        all_cards = repo.list_all()
        assert len(all_cards) == 2

        paper_only = repo.list_all("paper")
        assert len(paper_only) == 2


def test_load_missing_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        repo = CardRepository(Path(tmp))
        assert repo.load("paper", date(2026, 1, 1)) is None


def test_exists():
    with tempfile.TemporaryDirectory() as tmp:
        repo = CardRepository(Path(tmp))
        card = Card(id="paper_20260617", type=CardType.PAPER,
                     date=date(2026, 6, 17), items=[])
        repo.save(card)
        assert repo.exists("paper", date(2026, 6, 17))
        assert not repo.exists("paper", date(2026, 6, 18))
