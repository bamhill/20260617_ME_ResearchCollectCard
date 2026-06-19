"""CrossRef API fetcher for journal papers."""

from datetime import date
import httpx
from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem

CROSSREF_WORKS_URL = "https://api.crossref.org/journals/{issn}/works"


class CrossrefFetcher(AbstractFetcher):
    """Fetch journal papers from CrossRef API by ISSN.

    Source.query must be the journal ISSN (e.g. "0950-7051").
    """

    @property
    def source_type(self) -> str:
        return "crossref"

    def fetch(self, source: Source, target_date: date) -> list[RawItem]:
        issn = (source.query or "").strip()
        if not issn:
            return []

        date_str = target_date.strftime("%Y-%m-%d")
        url = (
            f"{CROSSREF_WORKS_URL.format(issn=issn)}"
            f"?filter=from-pub-date:{date_str},until-pub-date:{date_str}"
            f"&rows=20&sort=published&order=desc"
        )

        try:
            resp = httpx.get(url, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        items = data.get("message", {}).get("items", [])
        return [self._parse_item(item, source) for item in items]

    def _parse_item(self, raw: dict, source: Source) -> RawItem:
        # Title
        title_list = raw.get("title") or ["Untitled"]
        title = title_list[0] if title_list else "Untitled"

        # Authors
        authors_raw = raw.get("author") or []
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in authors_raw
        ]

        # DOI → URL
        doi = raw.get("DOI", "")
        url = raw.get("URL") or (f"https://doi.org/{doi}" if doi else "")

        # Date
        pub = None
        date_parts = raw.get("published-print", {}).get("date-parts", [[]])[0]
        if not date_parts:
            date_parts = raw.get("published-online", {}).get("date-parts", [[]])[0]
        if not date_parts:
            date_parts = raw.get("created", {}).get("date-parts", [[]])[0]
        if len(date_parts) >= 3:
            pub = date(date_parts[0], date_parts[1], date_parts[2])
        elif len(date_parts) == 2:
            pub = date(date_parts[0], date_parts[1], 1)

        # Abstract
        abstract = raw.get("abstract", "")

        return RawItem(
            title=title,
            authors=authors,
            url=url,
            published=pub,
            summary_raw=abstract,
            source_id=source.id,
            tags=list(source.tags),
        )
