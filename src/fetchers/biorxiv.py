"""bioRxiv API fetcher."""

from datetime import date
import httpx
from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem

BIORXIV_API = "https://api.biorxiv.org/details/biorxiv"


class BiorxivFetcher(AbstractFetcher):
    """Fetch papers from bioRxiv API."""

    @property
    def source_type(self) -> str:
        return "biorxiv"

    def fetch(self, source: Source, target_date: date) -> list[RawItem]:
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{BIORXIV_API}/{date_str}/{date_str}/0"

        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        data = response.json()
        collection = data.get("collection", [])
        items: list[RawItem] = []

        for paper in collection:
            title = paper.get("title", "Untitled")
            authors_str = paper.get("authors", "")
            authors = [a.strip() for a in authors_str.split(";") if a.strip()]
            doi = paper.get("doi", "")
            paper_url = f"https://www.biorxiv.org/content/{doi}" if doi else ""
            abstract = paper.get("abstract", "")
            paper_date_str = paper.get("date", "")
            published = None
            if paper_date_str:
                try:
                    published = date.fromisoformat(paper_date_str)
                except ValueError:
                    pass

            items.append(RawItem(
                title=title,
                authors=authors,
                url=paper_url,
                published=published,
                summary_raw=abstract,
                source_id=source.id,
            ))

        return items
