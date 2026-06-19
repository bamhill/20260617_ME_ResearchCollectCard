"""CardRepository: persist and retrieve generated cards as JSON files."""

from datetime import date
from pathlib import Path
from src.models import Card, CardMeta


class CardRepository:
    """CRUD for cards stored as JSON files under data/cards/."""

    def __init__(self, data_dir: Path):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _filename(self, card_type: str, d: date) -> str:
        return f"{card_type}_{d.strftime('%Y%m%d')}.json"

    def save(self, card: Card) -> Path:
        """Save a card to a JSON file. Returns the file path."""
        path = self._dir / self._filename(card.type.value, card.date)
        path.write_text(
            card.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load(self, card_type: str, d: date) -> Card | None:
        """Load a card by type and date. Returns None if not found."""
        path = self._dir / self._filename(card_type, d)
        if not path.exists():
            return None
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return Card.model_validate(data)

    def list_all(self, card_type: str | None = None) -> list[CardMeta]:
        """List all cards, optionally filtered by type. Returns CardMeta list."""
        results: list[CardMeta] = []
        for p in sorted(self._dir.glob("*.json"), reverse=True):
            stem = p.stem
            if card_type and not stem.startswith(card_type):
                continue
            import json
            data = json.loads(p.read_text(encoding="utf-8"))
            card = Card.model_validate(data)
            results.append(card.to_meta())
        return results

    def exists(self, card_type: str, d: date) -> bool:
        return (self._dir / self._filename(card_type, d)).exists()
