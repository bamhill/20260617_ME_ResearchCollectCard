"""FetchPipeline: orchestrate fetching from multiple sources."""

from src.fetchers.base import AbstractFetcher
from src.models import Source, RawItem, Card, CardType, DateRange, PaperItem, WechatItem


class FetchPipeline:
    """Orchestrates fetching from multiple sources.

    Iterates over sources for a card type, dispatches to the correct
    fetcher, and collects results into Card objects.
    """

    def __init__(self, fetchers: dict[str, AbstractFetcher]):
        self._fetchers = fetchers

    def run(self, card_type: str, sources: list[Source], date_range: DateRange) -> list[Card]:
        cards: list[Card] = []
        for d in date_range.dates():
            all_items: list[RawItem] = []
            for source in sources:
                fetcher = self._fetchers.get(source.type.value)
                if fetcher is None:
                    continue
                items = fetcher.fetch(source, d)
                for item in items:
                    item.source_id = source.id
                    item.tags = source.tags
                all_items.extend(items)

            # Convert RawItem → PaperItem / WechatItem for Card type safety
            item_cls = PaperItem if card_type == "paper" else WechatItem
            typed_items = [item_cls(**item.model_dump()) for item in all_items]

            card = Card(
                id=f"{card_type}_{d.strftime('%Y%m%d')}",
                type=CardType(card_type),
                date=d,
                date_range=date_range if len(date_range.dates()) > 1 else None,
                items=typed_items,
            )
            cards.append(card)

        return cards
