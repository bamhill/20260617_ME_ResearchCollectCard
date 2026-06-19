"""RSS feed fetcher for WeChat public accounts and journal feeds."""

import re
from datetime import date, datetime, timezone
import feedparser
from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem

#: Regexes to extract date from summary text (publisher RSS fallback).
_DATE_PATTERNS = [
    re.compile(r"Publication date:\s*(\d{1,2}\s+\w+\s+\d{4})", re.IGNORECASE),
    re.compile(r"Published:\s*(\d{1,2}\s+\w+\s+\d{4})", re.IGNORECASE),
    re.compile(r"Date:\s*(\d{1,2}\s+\w+\s+\d{4})", re.IGNORECASE),
]


class RssFetcher(AbstractFetcher):
    """Fetch articles from RSS feeds (WeChat / journal publisher RSS)."""

    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    @property
    def source_type(self) -> str:
        return "rss"

    def fetch(self, source: Source, target_date: date) -> list[RawItem]:
        if not source.query:
            return []

        rss_url = source.query
        try:
            feed = feedparser.parse(rss_url)
        except Exception:
            return []

        if feed.bozo and not feed.entries:
            return []

        items: list[RawItem] = []
        for entry in feed.entries:
            published = self._parse_date(entry)
            if published and published.date() != target_date:
                continue

            title = entry.get("title", "Untitled").strip()
            if self._is_meta_entry(title):
                continue
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))
            summary_text = re.sub(r"<[^>]+>", "", summary).strip()
            author = entry.get("author", source.name)

            items.append(RawItem(
                title=title,
                authors=[author],
                url=link,
                published=published.date() if published else None,
                summary_raw=summary_text,
                source_id=source.id,
            ))

        return items

    def _parse_date(self, entry) -> datetime | None:
        for field in ("published_parsed", "updated_parsed"):
            tp = entry.get(field)
            if tp and len(tp) >= 6:
                try:
                    return datetime(*tp[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    continue
        return self._parse_date_from_summary(entry)

    def _parse_date_from_summary(self, entry) -> datetime | None:
        """Fallback: extract date from summary/html text (Elsevier, etc.)."""
        summary = entry.get("summary", entry.get("description", ""))
        if not summary:
            return None
        text = re.sub(r"<[^>]+>", "", summary)
        for pat in _DATE_PATTERNS:
            m = pat.search(text)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), "%d %B %Y")
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _is_meta_entry(title: str) -> bool:
        """Filter out non-paper entries (TOC, editorial, etc.)."""
        skip = {"table of contents", "editorial", "front matter", "cover",
                "back cover", "call for papers", "special issue",
                "announcement", "corrigendum", "erratum"}
        return title.lower().strip() in skip
