"""RSS feed fetcher for WeChat public accounts."""

import re
from datetime import date, datetime, timezone
import feedparser
from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem


class RssFetcher(AbstractFetcher):
    """Fetch articles from RSS feeds (WeChat public accounts via WeRSS/Feeddd)."""

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
        return None
