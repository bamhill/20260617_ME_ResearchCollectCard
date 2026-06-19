"""Tests for hotspot extraction module."""

from src.hotspot import (
    _clean_phrase,
    _is_valid_phrase,
    _phrase_matches,
    _match_methods_to_items,
    _build_item_text,
)


class TestCleanPhrase:
    def test_lowercase(self):
        assert _clean_phrase("Large Language Models") == "large language models"

    def test_strip_whitespace(self):
        assert _clean_phrase("  extra   spaces  ") == "extra spaces"


class TestIsValidPhrase:
    def test_too_short(self):
        assert not _is_valid_phrase("ab")

    def test_punctuation_only(self):
        assert not _is_valid_phrase("123!")

    def test_noise_words(self):
        for w in ["the", "and", "for", "that", "this", "paper", "based", "using"]:
            assert not _is_valid_phrase(w), f"'{w}' should be noise"

    def test_valid_phrase(self):
        assert _is_valid_phrase("large language models")
        assert _is_valid_phrase("reinforcement learning")


class TestPhraseMatches:
    def test_exact_match(self):
        text = "we propose a novel diffusion model for image generation"
        assert _phrase_matches("diffusion model", text)

    def test_no_match(self):
        text = "we study transformer architectures"
        assert not _phrase_matches("diffusion model", text)

    def test_partial_two_words(self):
        text = "using proximal policy for optimization"
        assert _phrase_matches("proximal policy optimization", text)

    def test_single_long_word(self):
        text = "we use transformer for encoding"
        assert _phrase_matches("transformer", text)

    def test_short_word_substring_match(self):
        # "rl" is short but appears as substring
        text = "we use rl for training"
        assert _phrase_matches("rl", text)

    def test_short_word_no_substring(self):
        text = "we use reinforcement learning"
        # "xyz" doesn't appear, too short for word-level matching
        assert not _phrase_matches("xyz", text)


class TestMatchMethodsToItems:
    def test_single_method_mapping(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Gradient-based knowledge distillation"
        item.summary_raw = "We use gradient knowledge distillation to compress models"

        result = _match_methods_to_items(
            [["梯度知识蒸馏", "gradient knowledge distillation"]],
            [item],
        )
        assert len(result) == 1
        assert result[0].name == "梯度知识蒸馏"
        assert result[0].matched_indices == [0]

    def test_merge_duplicate_names(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Knowledge Distillation for LLMs"
        item.summary_raw = "distillation and language models"

        result = _match_methods_to_items(
            [["知识蒸馏", "knowledge distillation"], ["知识蒸馏", "distillation"]],
            [item],
        )
        assert len(result) == 1  # merged
        assert result[0].name == "知识蒸馏"
        assert result[0].matched_indices == [0]

    def test_old_format_fallback(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Transformer study"
        item.summary_raw = ""

        result = _match_methods_to_items(["transformer"], [item])
        assert len(result) == 1
        assert result[0].matched_indices == [0]

    def test_no_match(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Unrelated Study"
        item.summary_raw = "nothing about graphs"

        result = _match_methods_to_items(
            [["图神经网络", "graph neural network"]],
            [item],
        )
        assert result[0].matched_indices == []


class TestBuildItemText:
    def test_concatenates_title_and_summary(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Title"
        item.summary_raw = "Abstract text"
        text = _build_item_text(item)
        assert "Title" in text
        assert "Abstract text" in text

    def test_no_summary(self):
        class FakeItem:
            pass
        item = FakeItem()
        item.title = "Title Only"
        item.summary_raw = ""
        text = _build_item_text(item)
        assert text == "Title Only"
