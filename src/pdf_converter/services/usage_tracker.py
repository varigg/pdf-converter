"""Persistent monthly usage accounting for LLM requests."""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from platformdirs import user_state_path

LOGGER = logging.getLogger(__name__)
DEFAULT_USAGE_FILE = user_state_path("pdf-converter", "varigg") / "usage_stats.json"
PathLike = str | os.PathLike[str]


class UsageTracker:
    """Track request counts, token usage, and estimated cost by provider."""

    def __init__(self, provider: str = "unknown", filepath: PathLike = DEFAULT_USAGE_FILE):
        self.provider = provider
        self.filepath = Path(filepath)
        self.stats = self._load_stats()

    def _load_stats(self) -> dict[str, Any]:
        if not self.filepath.is_file():
            return {}
        try:
            with self.filepath.open(encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            LOGGER.warning("Could not read usage statistics from %s", self.filepath)
            return {}
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}

    def _save_stats(self) -> None:
        temporary_path: Path | None = None
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.filepath.parent,
                prefix=f".{self.filepath.name}.",
                delete=False,
            ) as temporary_file:
                json.dump(self.stats, temporary_file, indent=2)
                temporary_file.write("\n")
                temporary_path = Path(temporary_file.name)
            os.replace(temporary_path, self.filepath)
        except OSError:
            LOGGER.warning("Could not save usage statistics to %s", self.filepath)
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def track_request(self, tokens: int = 0, cost: float = 0.0) -> None:
        """Record one request for this tracker's provider."""
        self.stats = self._load_stats()
        month = datetime.now().strftime("%Y-%m")
        month_stats = self.stats.setdefault(month, {})
        provider_stats = month_stats.setdefault(
            self.provider,
            {"requests": 0, "tokens": 0, "cost": 0.0},
        )
        provider_stats["requests"] += 1
        provider_stats["tokens"] += tokens
        provider_stats["cost"] += cost
        self._save_stats()

    def get_stats(self, month: str | None = None, provider: str | None = None) -> dict[str, Any]:
        """Return all statistics or one provider's statistics for a month."""
        self.stats = self._load_stats()
        if month is None:
            return self.stats
        target_provider = provider or self.provider
        month_stats = self.stats.get(month, {})
        return cast(
            dict[str, Any],
            month_stats.get(target_provider, {"requests": 0, "tokens": 0, "cost": 0.0}),
        )

    def get_current_month_stats(self, provider: str | None = None) -> dict[str, Any]:
        """Return current-month statistics for one provider."""
        return self.get_stats(datetime.now().strftime("%Y-%m"), provider)

    def get_all_providers_stats(self, month: str | None = None) -> dict[str, Any]:
        """Return all provider statistics for a month."""
        self.stats = self._load_stats()
        target_month = month or datetime.now().strftime("%Y-%m")
        return cast(dict[str, Any], self.stats.get(target_month, {}))
