"""Tests for Config loader."""

import json
import tempfile
from pathlib import Path
from src.config import Config


def test_load_minimal_config():
    data = {
        "paper_sources": [
            {"id": "test_arxiv", "name": "Test arXiv", "type": "arxiv", "query": "cat:cs.CL", "tags": []}
        ],
        "wechat_sources": [
            {"id": "test_rss", "name": "Test RSS", "type": "rss", "query": "https://example.com/feed", "tags": []}
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        tmp_path = f.name

    try:
        config = Config.load(tmp_path)
        assert len(config.paper_sources) == 1
        assert config.paper_sources[0].id == "test_arxiv"
        assert len(config.wechat_sources) == 1
        assert config.wechat_sources[0].name == "Test RSS"
    finally:
        Path(tmp_path).unlink()


def test_get_sources_by_type():
    data = {
        "paper_sources": [
            {"id": "arxiv1", "name": "ArXiv", "type": "arxiv", "query": "cat:cs.CL", "tags": []}
        ],
        "wechat_sources": [
            {"id": "rss1", "name": "RSS", "type": "rss", "query": "https://x.com/feed", "tags": []}
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        tmp_path = f.name

    try:
        config = Config.load(tmp_path)
        assert len(config.get_sources("arxiv")) == 1
        assert len(config.get_sources("rss")) == 1
    finally:
        Path(tmp_path).unlink()
