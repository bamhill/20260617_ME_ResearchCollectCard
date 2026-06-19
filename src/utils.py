"""Shared utilities for API configuration."""

import os


def deepseek_api_key() -> str:
    """Return DeepSeek API key from environment."""
    return os.environ.get("DEEPSEEK_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
