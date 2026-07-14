import json
from datetime import datetime
from pathlib import Path

from pdf_converter.services.usage_tracker import UsageTracker


def test_usage_tracker_persists_provider_stats(tmp_path: Path) -> None:
    usage_file = tmp_path / "state" / "usage.json"
    tracker = UsageTracker("openai", usage_file)

    tracker.track_request(tokens=12, cost=0.5)

    current_month = datetime.now().strftime("%Y-%m")
    assert tracker.get_current_month_stats() == {"requests": 1, "tokens": 12, "cost": 0.5}
    assert json.loads(usage_file.read_text(encoding="utf-8"))[current_month]["openai"]["tokens"] == 12


def test_usage_tracker_recovers_from_invalid_json(tmp_path: Path) -> None:
    usage_file = tmp_path / "usage.json"
    usage_file.write_text("not json", encoding="utf-8")

    tracker = UsageTracker("openai", usage_file)

    assert tracker.get_current_month_stats() == {"requests": 0, "tokens": 0, "cost": 0.0}
