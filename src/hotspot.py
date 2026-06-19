"""Hotspot extraction: YAKE keyword extraction + DeepSeek translation/classification."""

import json
import re
from collections import Counter, defaultdict

import httpx
import yake

from src.models import Hotspots, MethodEntry
from src.utils import deepseek_api_key

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

CLASSIFY_PROMPT = (
    "你将收到一组从英文学术论文摘要中提取的关键短语。请完成：\n\n"
    "1. 写一句「主题总结」（30字内）：概括这批论文共同关注的研究领域。\n"
    "2. 将短语分为两类并翻译：\n"
    "   - themes（研究主题）：论文研究的问题、领域、对象\n"
    "   - methods（技术方法）：论文使用的技术、算法、方法论\n\n"
    "**重要**：每个 method 需要同时给出中文译名和其对应的原始英文短语，"
    "用英文原文方便后续匹配。格式：\n"
    '{{"summary": "...",\n'
    ' "themes": ["主题1", ...],\n'
    ' "methods": [["方法中文", "english phrase"], ...]}}\n\n'
    "例如：methods: [[\"扩散模型\", \"diffusion models\"], [\"思维链\", \"chain of thought\"]]\n\n"
    "规则：每个短语只归入一类，翻译2-6字。不确定归 themes。\n"
    "只输出 JSON，不要 markdown。\n\n"
    "关键短语：\n{phrases}"
)

YAKE_KW_EXTRACTOR = yake.KeywordExtractor(
    lan="en", n=3, dedupLim=0.9, top=8, features=None,
)


def extract_hotspots(items, api_key: str | None = None, top_n: int = 15) -> Hotspots | None:
    """Extract hot topics with article-level method mapping.

    1. YAKE per-item → aggregate scored English keyphrases
    2. DeepSeek: translate + classify + summary, preserving English source for methods
    3. Match methods to articles using the English source phrase

    Returns Hotspots or None.
    """
    if len(items) < 3:
        return None

    key = api_key or deepseek_api_key()
    if not key:
        return None

    # 1. YAKE per-item, track which items yielded each phrase
    phrase_scores: Counter[str] = Counter()
    for item in items:
        text = _build_item_text(item)
        if not text.strip():
            continue
        try:
            for kw, score in YAKE_KW_EXTRACTOR.extract_keywords(text):
                clean = _clean_phrase(kw)
                if _is_valid_phrase(clean):
                    phrase_scores[clean] += 1.0 / max(score, 0.001)
        except Exception:
            continue

    if not phrase_scores:
        return None

    phrases = [p for p, _ in phrase_scores.most_common(top_n)]

    # 2. DeepSeek classify
    try:
        classified = _classify_via_deepseek(phrases, key)
    except Exception:
        return None

    if not classified:
        return None

    # 3. Match methods to articles using English source phrase
    method_entries = _match_methods_to_items(
        classified.get("methods", []),
        items,
    )

    return Hotspots(
        theme_summary=classified.get("summary", ""),
        themes=classified.get("themes", []),
        methods=method_entries,
    )


def _match_methods_to_items(methods_raw: list, items) -> list[MethodEntry]:
    """For each method [cn_name, en_phrase], find article indices where
    the English phrase appears in title or abstract.

    Duplicate Chinese names are merged (different English phrases → same CN name).
    """
    merged: dict[str, set[int]] = defaultdict(set)
    order: list[str] = []  # preserve first-seen order

    for entry in methods_raw:
        if isinstance(entry, str):
            cn_name, en_phrase = entry, entry.lower()
        elif isinstance(entry, list) and len(entry) >= 2:
            cn_name, en_phrase = entry[0], entry[1].lower()
        else:
            continue

        if cn_name not in merged:
            order.append(cn_name)

        for idx, item in enumerate(items):
            text = _build_item_text(item).lower()
            if _phrase_matches(en_phrase, text):
                merged[cn_name].add(idx)

    return [MethodEntry(name=cn, matched_indices=sorted(merged[cn])) for cn in order]


def _phrase_matches(en_phrase: str, item_text: str) -> bool:
    """Check if an English keyphrase matches item text.

    Tries exact phrase match first, then individual content words.
    """
    if en_phrase in item_text:
        return True

    # Split into words and try matching significant words (length >= 3)
    words = [w for w in en_phrase.split() if len(w) >= 3]
    if len(words) >= 2:
        return sum(1 for w in words if w in item_text) >= 2
    if len(words) == 1 and len(words[0]) >= 4:
        return words[0] in item_text
    return False


def _build_item_text(item) -> str:
    parts = [item.title]
    summary = getattr(item, "summary_raw", "") or ""
    if summary:
        parts.append(summary[:500])
    return " ".join(parts)


def _clean_phrase(phrase: str) -> str:
    return " ".join(phrase.lower().strip().split())


def _is_valid_phrase(phrase: str) -> bool:
    if len(phrase) < 3:
        return False
    if re.match(r'^[\d\W_]+$', phrase):
        return False
    noise = {"the", "and", "for", "that", "this", "with", "from", "have",
             "been", "were", "are", "was", "not", "but", "can", "has", "had",
             "its", "our", "may", "also", "new", "one", "two", "use", "used",
             "using", "based", "show", "shown", "paper", "proposed"}
    return phrase not in noise


def _classify_via_deepseek(phrases: list[str], api_key: str) -> dict:
    phrases_text = "\n".join(f"- {p}" for p in phrases)

    resp = httpx.post(
        DEEPSEEK_API_URL,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": CLASSIFY_PROMPT.format(phrases=phrases_text)},
            ],
            "max_tokens": 512,
            "temperature": 0.1,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip ```json ... ``` fences if present
    content = re.sub(r"^```(?:json)?\s*\n?", "", content)
    content = re.sub(r"\n?```\s*$", "", content)

    return json.loads(content)
