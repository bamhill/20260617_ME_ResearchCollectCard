"""Load and manage sources.json configuration."""

from pathlib import Path
from src.models import Source


class Config:
    """Typed wrapper around sources.json."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._load()

    def _load(self) -> None:
        import json
        if not self._path.exists():
            raise FileNotFoundError(f"sources.json not found at {self._path}")
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self.paper_sources: list[Source] = [
            Source.model_validate(s) for s in data.get("paper_sources", [])
        ]
        self.wechat_sources: list[Source] = [
            Source.model_validate(s) for s in data.get("wechat_sources", [])
        ]

    @classmethod
    def load(cls, path: str | Path = "sources.json") -> "Config":
        return cls(Path(path))

    def get_sources(self, source_type: str) -> list[Source]:
        if source_type in ("arxiv", "biorxiv", "crossref"):
            return [s for s in self.paper_sources if s.type.value == source_type]
        if source_type == "rss":
            return list(self.wechat_sources)
        raise ValueError(f"Unknown source type: {source_type}")

    def top_conference_sources(self) -> list[Source]:
        """Return only sources tagged as 顶会 (top conferences)."""
        return [s for s in self.paper_sources if "顶会" in s.tags]

    def cs_sources(self) -> list[Source]:
        """Return arXiv CS category sources (non-conference)."""
        return [s for s in self.paper_sources if s.type.value == "arxiv" and "顶会" not in s.tags]

    def journal_sources(self) -> list[Source]:
        """Return CrossRef journal sources."""
        return [s for s in self.paper_sources if s.type.value == "crossref"]

    def all_paper_sources(self) -> list[Source]:
        return list(self.paper_sources)

    def all_wechat_sources(self) -> list[Source]:
        return list(self.wechat_sources)

    def add_source(self, source: Source) -> None:
        if source.type.value in ("arxiv", "biorxiv", "crossref"):
            self.paper_sources.append(source)
        else:
            self.wechat_sources.append(source)
        self._save()

    def remove_source(self, source_id: str) -> bool:
        for lst in [self.paper_sources, self.wechat_sources]:
            for i, s in enumerate(lst):
                if s.id == source_id:
                    lst.pop(i)
                    self._save()
                    return True
        return False

    def _save(self) -> None:
        import json
        data = {
            "paper_sources": [s.model_dump() for s in self.paper_sources],
            "wechat_sources": [s.model_dump() for s in self.wechat_sources],
        }
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
