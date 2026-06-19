"""ArXiv API fetcher."""

from datetime import date
import httpx
from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem

ARXIV_API_BASE = "https://export.arxiv.org/api/query"


class ArxivFetcher(AbstractFetcher):
    """Fetch papers from arXiv API."""

    @property
    def source_type(self) -> str:
        return "arxiv"

    def fetch(self, source: Source, target_date: date) -> list[RawItem]:
        query = source.query or "cat:cs.CL"
        date_str = target_date.strftime("%Y%m%d")
        search_query = (
            f"search_query={query}+AND+submittedDate:[{date_str}0000+TO+{date_str}2359]"
            f"&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending"
        )
        url = f"{ARXIV_API_BASE}?{search_query}"

        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        return self._parse_atom(response.text, source.id, target_date)

    def _parse_atom(self, xml_text: str, source_id: str, target_date: date) -> list[RawItem]:
        """Parse arXiv Atom XML response into RawItem list."""
        import xml.etree.ElementTree as ET

        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        items: list[RawItem] = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else "Untitled"

            summary_el = entry.find("atom:summary", ns)
            summary = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""

            id_el = entry.find("atom:id", ns)
            arxiv_url = id_el.text.strip() if id_el is not None and id_el.text else ""
            paper_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""

            authors: list[str] = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            published_el = entry.find("atom:published", ns)
            published = None
            if published_el is not None and published_el.text:
                try:
                    published = date.fromisoformat(published_el.text[:10])
                except ValueError:
                    pass

            items.append(RawItem(
                title=title,
                authors=authors,
                url=arxiv_url,
                published=published,
                summary_raw=summary,
                source_id=source_id,
            ))

        return items
