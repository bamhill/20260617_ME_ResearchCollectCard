"""Abstract base for all content fetchers."""

from abc import ABC, abstractmethod
from datetime import date
from src.models import Source, RawItem


class AbstractFetcher(ABC):
    """Strategy interface for content fetching.

    Each implementation handles one source type (arXiv, bioRxiv, RSS).
    New sources = new implementation of this interface.
    """

    @abstractmethod
    def fetch(self, source: Source, target_date: date) -> list[RawItem]:
        """Fetch items from `source` for `target_date`.

        Args:
            source: The source configuration from sources.json.
            target_date: The date to fetch content for.

        Returns:
            List of RawItem objects. Empty list if nothing found or on error.
        """
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """The source type this fetcher handles ('arxiv', 'biorxiv', 'rss')."""
        ...
