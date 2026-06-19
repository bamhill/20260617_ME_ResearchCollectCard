"""TransformPipeline: deduplicate, sort, enrich, and hotspot-extract."""

import httpx
from src.models import Card, PaperItem
from src.hotspot import extract_hotspots
from src.utils import deepseek_api_key

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

TRANSLATE_PROMPT = (
    "你是一个学术翻译助手。请将以下英文学术论文摘要翻译成简洁、准确的中文。"
    "只输出翻译后的中文，不要加任何解释、前缀或后缀。"
    "控制在100字以内。\n\n"
    "英文摘要：\n{text}"
)


class TransformPipeline:
    """Post-processing transforms on fetched cards."""

    def run(self, cards: list[Card], translate: bool = False, topic: str | None = None) -> list[Card]:
        for card in cards:
            card.items = self._dedup_by_url(card.items)
            card.items = sorted(card.items, key=lambda x: x.published or card.date, reverse=True)
            if topic:
                card.items = self._filter_by_topic(card.items, topic)
            if translate and card.type.value == "paper":
                card.items = self._translate_summaries(card.items)
            # Hotspot extraction for paper cards with enough items
            if card.type.value == "paper":
                card.hotspots = extract_hotspots(card.items)
        return cards

    @staticmethod
    def _filter_by_topic(items, topic: str):
        """Keep items whose tags contain ALL space-separated topic words (AND)."""
        topics = topic.split()
        return [item for item in items
                if all(t in (getattr(item, "tags", []) or []) for t in topics)]

    @staticmethod
    def _dedup_by_url(items):
        seen = set()
        result = []
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                result.append(item)
        return result

    def _translate_summaries(self, items):
        """Translate English abstracts to Chinese for paper items.

        Only translates items where summary_raw is non-empty and summary_zh
        is still empty. WeChat items (already Chinese) are skipped by the
        caller checking card.type.
        """
        for item in items:
            if not isinstance(item, PaperItem):
                continue
            if not item.summary_raw or item.summary_zh:
                continue
            try:
                item.summary_zh = self._translate_one(item.summary_raw)
            except Exception:
                # Translation failure doesn't block the pipeline
                pass
        return items

    def _translate_one(self, text: str) -> str:
        """Translate a single abstract via DeepSeek API."""
        if not deepseek_api_key():
            return ""

        # Truncate very long abstracts before sending
        truncated = text[:800]

        resp = httpx.post(
            DEEPSEEK_API_URL,
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": TRANSLATE_PROMPT.format(text=truncated)},
                ],
                "max_tokens": 256,
                "temperature": 0.3,
            },
            headers={
                "Authorization": f"Bearer {deepseek_api_key()}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
