"""Tests for RenderPipeline."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch
from src.pipeline.render import RenderPipeline
from src.models import Card, CardType, PaperItem


def test_group_by_topic():
    items = [
        PaperItem(title="A", url="https://a.com", source_id="arxiv_cs_cl", tags=["大模型", "NLP"]),
        PaperItem(title="B", url="https://b.com", source_id="arxiv_cs_cl", tags=["大模型"]),
        PaperItem(title="C", url="https://c.com", source_id="arxiv_cs_ai", tags=["多模态"]),
    ]
    card = Card(id="test", type=CardType.PAPER, date=date(2026, 6, 17), items=items)
    sections = RenderPipeline._group_by_topic(card)
    assert len(sections) == 2  # 大模型(A+B), 多模态(C) — 去重后每篇只入首标签


def test_render_produces_html():
    with tempfile.TemporaryDirectory() as tmp:
        template_dir = Path(tmp) / "templates"
        template_dir.mkdir()
        (template_dir / "_base.html").write_text(
            '<!DOCTYPE html><html><body><div id="report">{% block content %}{% endblock %}</div>'
            '<button onclick="savePNG()">Save PNG</button></body></html>',
            encoding="utf-8"
        )
        (template_dir / "paper.html").write_text(
            '{% extends "_base.html" %}{% block content %}'
            '<h1>{{ card.date }}</h1><p>{{ card.item_count }} papers</p>'
            '{% for section in sections %}<h2>{{ section.label }}</h2>'
            '{% for item in section.entries %}<div>{{ item.title }}</div>{% endfor %}{% endfor %}'
            '{% endblock %}',
            encoding="utf-8"
        )

        output_dir = Path(tmp) / "out"
        pipeline = RenderPipeline(template_dir, output_dir)

        card = Card(
            id="paper_20260617",
            type=CardType.PAPER,
            date=date(2026, 6, 17),
            items=[
                PaperItem(title="Test Paper", url="https://example.com", source_id="test_source"),
            ],
        )

        with patch.object(pipeline, '_load_html2canvas', return_value="dGVzdA=="):
            path = pipeline.render(card)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Test Paper" in content
        assert "2026-06-17" in content
        assert "Save PNG" in content
