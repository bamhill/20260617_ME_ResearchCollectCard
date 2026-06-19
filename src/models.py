"""Pydantic v2 data models for ResearchCollectCard."""

from datetime import date, datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field


class CardType(str, Enum):
    PAPER = "paper"
    WECHAT = "wechat"


class SourceType(str, Enum):
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    RSS = "rss"
    CROSSREF = "crossref"


class Source(BaseModel):
    """A content source definition from sources.json."""
    id: str
    name: str
    type: SourceType
    query: str | None = None
    tags: list[str] = Field(default_factory=list)


class MethodEntry(BaseModel):
    """A technical method hot topic with links to matching articles."""
    name: str                                      # 中文方法名
    matched_indices: list[int] = Field(default_factory=list)  # card.items indices


class Hotspots(BaseModel):
    """Extracted hot topics grouped by research theme vs. technical method."""
    theme_summary: str = ""                              # 本期主题一句话总结
    themes: list[str] = Field(default_factory=list)      # 研究主题热点（中文）
    methods: list[MethodEntry] = Field(default_factory=list)  # 技术方法热点 + 文章映射


class RawItem(BaseModel):
    """Raw item produced by a fetcher, before transformation."""
    title: str
    authors: list[str] = Field(default_factory=list)
    url: str
    published: date | None = None
    summary_raw: str = ""
    summary_zh: str = ""
    source_id: str
    tags: list[str] = Field(default_factory=list)  # Topic tags inherited from source
    is_idea: bool = False  # Mark for promotion to idea library


class PaperItem(RawItem):
    """A paper item with arXiv/bioRxiv specific fields."""
    paper_id: str | None = None


class WechatItem(RawItem):
    """A WeChat public account article item."""
    mp_url: str | None = None


class DateRange(BaseModel):
    """A date range for fetching."""
    start: date
    end: date

    @classmethod
    def single(cls, d: date) -> "DateRange":
        return cls(start=d, end=d)

    def dates(self) -> list[date]:
        """Generate all dates in this range."""
        result = []
        current = self.start
        while current <= self.end:
            result.append(current)
            current += timedelta(days=1)
        return result


class CardMeta(BaseModel):
    """Lightweight card metadata for listing."""
    id: str
    type: CardType
    date: date
    generated_at: datetime
    item_count: int
    idea_count: int = 0  # Count of items with is_idea=True


class Card(BaseModel):
    """A complete generated card."""
    id: str
    type: CardType
    date: date
    generated_at: datetime = Field(default_factory=datetime.now)
    date_range: DateRange | None = None
    items: list[PaperItem | WechatItem] = Field(default_factory=list)
    hotspots: Hotspots | None = None

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def idea_count(self) -> int:
        return sum(1 for item in self.items if item.is_idea)

    def to_meta(self) -> CardMeta:
        return CardMeta(
            id=self.id,
            type=self.type,
            date=self.date,
            generated_at=self.generated_at,
            item_count=self.item_count,
            idea_count=self.idea_count,
        )
