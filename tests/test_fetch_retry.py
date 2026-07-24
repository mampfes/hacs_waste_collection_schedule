import asyncio
import os
import sys
from datetime import date
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule import Collection  # isort:skip
from waste_collection_schedule.source_shell import SourceShell  # isort:skip


def test_source_shell_fetch_reports_success_and_failure() -> None:
    class _Source:
        def __init__(self) -> None:
            self.should_fail = True

        def fetch(self):
            if self.should_fail:
                raise RuntimeError("temporary upstream failure")
            return [Collection(date=date(2026, 7, 20), t="Test collection")]

    source = _Source()
    shell = SourceShell(
        source=source,
        customize={},
        title="Test source",
        description="Test source",
        url=None,
        calendar_title=None,
        unique_id="test-source",
        day_offset=0,
    )

    assert shell.fetch() is False
    assert shell.refreshtime is None

    source.should_fail = False
    assert shell.fetch() is True
    assert shell.refreshtime is not None

    cached_entries = list(shell._entries)
    cached_refreshtime = shell.refreshtime
    source.should_fail = True

    assert shell.fetch() is False
    assert shell._entries == cached_entries
    assert shell.refreshtime is cached_refreshtime


def test_coordinator_allows_same_day_retry_after_failed_fetch() -> None:
    from custom_components.waste_collection_schedule import wcs_coordinator

    class _Hass:
        @staticmethod
        async def async_add_executor_job(target):
            return target()

    class _Shell:
        def __init__(self) -> None:
            self.fetch_results = iter((False, True))
            self.fetch_count = 0

        def fetch(self) -> bool:
            self.fetch_count += 1
            return next(self.fetch_results)

    async def _run() -> tuple[int, object]:
        coordinator = object.__new__(wcs_coordinator.WCSCoordinator)
        coordinator._hass = _Hass()
        coordinator._shell = cast(Any, _Shell())
        coordinator._last_fetch_date = None
        coordinator._fetch_interval_days = 1
        coordinator._update_sensors_callback = lambda *_: asyncio.sleep(0)

        with patch.object(wcs_coordinator, "get_device_key_store", return_value=None):
            await coordinator._fetch_now()
            assert coordinator._last_fetch_date is None

            await coordinator._fetch_now()
            assert coordinator._last_fetch_date is not None

            await coordinator._fetch_now()

        return coordinator.shell.fetch_count, coordinator._last_fetch_date

    fetch_count, last_fetch_date = asyncio.run(_run())

    assert fetch_count == 2
    assert last_fetch_date is not None


def test_coordinator_first_refresh_reports_failed_fetch() -> None:
    from custom_components.waste_collection_schedule import wcs_coordinator

    coordinator = object.__new__(wcs_coordinator.WCSCoordinator)
    coordinator._shell = cast(Any, type("Shell", (), {"title": "Test source"})())

    async def _run() -> None:
        with (
            patch.object(coordinator, "_fetch_now", AsyncMock(return_value=False)),
            pytest.raises(
                wcs_coordinator.UpdateFailed,
                match="Unable to fetch waste collection data from Test source",
            ),
        ):
            await coordinator._async_update_data()

    asyncio.run(_run())


def test_yaml_api_retries_all_sources_after_partial_failure() -> None:
    from custom_components.waste_collection_schedule.waste_collection_api import (
        WasteCollectionApi,
    )

    class _Shell:
        def __init__(self, *results: bool) -> None:
            self.fetch_results = iter(results)
            self.fetch_count = 0

        def fetch(self) -> bool:
            self.fetch_count += 1
            return next(self.fetch_results)

    successful_shell = _Shell(True, True)
    recovering_shell = _Shell(False, True)
    api = object.__new__(WasteCollectionApi)
    api._source_shells = cast(Any, [successful_shell, recovering_shell])
    api._last_fetch_date = None
    api._fetch_interval_days = 1
    api._update_sensors_callback = lambda *_: None

    api._fetch()
    assert api._last_fetch_date is None

    api._fetch()
    assert api._last_fetch_date is not None

    api._fetch()
    assert successful_shell.fetch_count == 2
    assert recovering_shell.fetch_count == 2
