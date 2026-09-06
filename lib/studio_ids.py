"""Resolve Discord channel IDs from the LOCAL studio registry.

The registry (~/.hermes/studio/projects.yaml) is machine-local state and is
never committed. Repos stay free of server identifiers; deploys read them at
runtime. Raises RuntimeError with a clear message when a key is missing.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REGISTRY = Path.home() / ".hermes" / "studio" / "projects.yaml"


def discord_id(key: str) -> str:
    data = yaml.safe_load(REGISTRY.read_text())
    try:
        val = data["settings"]["discord"][key]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Registry {REGISTRY} missing settings.discord.{key}"
        ) from exc
    if not val:
        raise RuntimeError(f"Registry {REGISTRY} has empty settings.discord.{key}")
    return str(val)


def ticker_channels() -> dict:
    return {
        sym: discord_id(f"{sym.lower()}_ticker_channel_id")
        for sym in ("BTC", "ETH", "SOL", "ZEC", "HYPE", "MANCER")
    }


def project_channel_id(slug: str) -> str:
    """Review/project channel for a studio project (e.g. #trend-threads)."""
    data = yaml.safe_load(REGISTRY.read_text())
    try:
        val = data["projects"][slug]["discord_channel_id"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Registry {REGISTRY} missing projects.{slug}.discord_channel_id"
        ) from exc
    if not val:
        raise RuntimeError(
            f"Registry {REGISTRY} has empty projects.{slug}.discord_channel_id")
    return str(val)
