"""Data written while ForexFactory used the "ig" key keeps working."""

import json
from datetime import datetime, timezone

from config.constants import PathConfig
from config.settings import Settings
from core.cache import CalendarCache
from core.exporters import render_ics
from core.models import CalendarSource


def test_legacy_ig_settings_are_migrated() -> None:
    PathConfig.SETTINGS_FILE.write_text(
        json.dumps(
            {
                "active_source": "ig",
                "ig_selected_region": "USA",
                "ig_selected_impact": "HIGH",
                "ig_sort_key": "impact",
                "ig_sort_direction": "desc",
                "ig_column_order": [1, 0, 2, 3, 4, 5, 6, 7],
                "last_refresh_ig": "2026-08-21T10:30:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    settings = Settings()
    settings.load()
    assert settings.get("active_source") == "forexfactory"
    assert settings.get("forexfactory_selected_region") == "USA"
    assert settings.get("forexfactory_selected_impact") == "HIGH"
    assert settings.get("forexfactory_sort_key") == "impact"
    assert settings.get("forexfactory_sort_direction") == "desc"
    assert settings.get("forexfactory_column_order")[:2] == [1, 0]

    assert settings.save()
    saved = json.loads(PathConfig.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert not any(key.startswith(("ig_", "last_refresh")) for key in saved)


def test_legacy_ig_cache_is_loaded_then_replaced() -> None:
    legacy = PathConfig.APP_DATA_DIR / "calendar_ig.json"
    legacy.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "ig",
                "refreshed_at": "2026-08-21T10:30:00+00:00",
                "events": [
                    {
                        "time": "12:30",
                        "country": "USA",
                        "impact": "HIGH",
                        "event_name": "Nonfarm Payrolls",
                        "actual": "",
                        "forecast": "120K",
                        "previous": "110K",
                        "date": "21/08/2026",
                        "utc_dt": "2026-08-21T12:30:00+00:00",
                        "deviation": "",
                        "source": "ig",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    cache = CalendarCache()
    snapshot = cache.load(CalendarSource.FOREXFACTORY)
    assert snapshot is not None
    assert snapshot.events[0].source == CalendarSource.FOREXFACTORY
    assert snapshot.events[0].event_name == "Nonfarm Payrolls"

    assert cache.save(
        CalendarSource.FOREXFACTORY, list(snapshot.events), snapshot.refreshed_at
    )
    assert not legacy.exists()
    current = PathConfig.APP_DATA_DIR / "calendar_forexfactory.json"
    assert json.loads(current.read_text(encoding="utf-8"))["source"] == "forexfactory"


def test_ics_uid_is_unchanged_by_the_rename() -> None:
    event = {
        "source": "forexfactory",
        "utc_dt": "2026-08-21T12:30:00+00:00",
        "country": "USA",
        "event_name": "Nonfarm Payrolls",
    }
    stamp = datetime(2026, 8, 20, tzinfo=timezone.utc)
    renamed = render_ics([event], generated_at=stamp)
    legacy = render_ics([{**event, "source": "ig"}], generated_at=stamp)
    uid = [line for line in renamed.splitlines() if line.startswith("UID:")]
    assert uid == [line for line in legacy.splitlines() if line.startswith("UID:")]
    # Value produced before the rename for the same event.
    assert uid == ["UID:" + _uid_before_rename(event) + "@financial-calendar"]


def _uid_before_rename(event: dict) -> str:
    import hashlib

    stable = "|".join(["ig", event["utc_dt"], event["country"], event["event_name"]])
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]
