import asyncio
import os
import sys
from datetime import date
from threading import Event
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

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


@pytest.mark.asyncio
async def test_coordinator_allows_same_day_retry_after_failed_fetch(ha) -> None:
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule import wcs_coordinator

    class _Source:
        def __init__(self) -> None:
            self.fetch_count = 0

        def fetch(self):
            self.fetch_count += 1
            if self.fetch_count == 1:
                raise RuntimeError("temporary upstream failure")
            return [Collection(date=date(2099, 1, 1), t="Test collection")]

    source = _Source()
    shell = SourceShell(
        source, {}, "Test source", "Test source", None, None, "retry", 0
    )
    coordinator = wcs_coordinator.WCSCoordinator(
        ha, entry_for(ha, {}), shell, ", ", "01:00", 1, 0, "10:00"
    )
    try:
        assert await coordinator._fetch_now() is False
        assert coordinator._last_fetch_date is None
        assert await coordinator._fetch_now() is True
        assert coordinator._last_fetch_date == date.today()
        assert await coordinator._fetch_now() is True
        assert source.fetch_count == 2
        assert coordinator._aggregator.get_upcoming()[0].date == date(2099, 1, 1)
    finally:
        await coordinator.async_shutdown()


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


def test_coordinator_starts_timers_only_after_successful_fetch() -> None:
    from custom_components.waste_collection_schedule import wcs_coordinator

    coordinator = object.__new__(wcs_coordinator.WCSCoordinator)
    coordinator._shell = cast(Any, type("Shell", (), {"title": "Test source"})())
    coordinator._async_track_timers = Mock()

    async def _run() -> None:
        with (
            patch.object(coordinator, "_fetch_now", AsyncMock(return_value=False)),
            pytest.raises(wcs_coordinator.UpdateFailed),
        ):
            await coordinator._async_update_data()
        coordinator._async_track_timers.assert_not_called()

        with patch.object(coordinator, "_fetch_now", AsyncMock(return_value=True)):
            await coordinator._async_update_data()
        coordinator._async_track_timers.assert_called_once_with()

    asyncio.run(_run())


def test_coordinator_shutdown_cancels_custom_timers() -> None:
    from custom_components.waste_collection_schedule import wcs_coordinator

    coordinator = object.__new__(wcs_coordinator.WCSCoordinator)
    unsubs = [Mock() for _ in range(4)]
    (
        coordinator._fetch_tracker,
        coordinator._day_switch_tracker,
        coordinator._midnight_tracker,
        coordinator._fetch_later_unsub,
    ) = unsubs

    coordinator._async_unsub_timers()

    for unsub in unsubs:
        unsub.assert_called_once_with()
    assert coordinator._fetch_tracker is None
    assert coordinator._day_switch_tracker is None
    assert coordinator._midnight_tracker is None
    assert coordinator._fetch_later_unsub is None


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


@pytest.mark.asyncio
@pytest.mark.parametrize("slow", [False, True])
@pytest.mark.parametrize("succeeds", [False, True])
async def test_provider_fetch_warning_is_delayed_once_and_cleared_on_completion(
    ha, monkeypatch, caplog, slow, succeeds
):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule import wcs_coordinator

    started = asyncio.Event()
    release = Event()

    class Source:
        def fetch(self):
            ha.loop.call_soon_threadsafe(started.set)
            if not release.wait(timeout=10):
                raise TimeoutError("Test did not release provider")
            if not succeeds:
                raise RuntimeError("Synthetic provider outage")
            return [Collection(date=date(2099, 1, 1), t="Paper")]

    shell = SourceShell(
        Source(), {}, "Test source", "Test source", None, None, "slow", 0
    )
    coordinator = wcs_coordinator.WCSCoordinator(
        ha, entry_for(ha, {}), shell, ", ", "01:00", 1, 0, "10:00"
    )
    loop_time = ha.loop.time
    elapsed = 0
    caplog.set_level("WARNING", logger=wcs_coordinator.__name__)

    def warnings():
        return [
            r.getMessage() for r in caplog.records if r.name == wcs_coordinator.__name__
        ]

    async def advance(seconds):
        nonlocal elapsed
        elapsed += seconds
        # Let the real event loop dispatch timers made due by the clock change.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    with monkeypatch.context() as clock:
        clock.setattr(ha.loop, "time", lambda: loop_time() + elapsed)
        task = ha.async_create_task(coordinator._fetch_now())
        try:
            await asyncio.wait_for(started.wait(), timeout=5)
            await advance(119)
            assert warnings() == []
            if slow:
                await advance(2)
                assert len(warnings()) == 1
                assert "Test source" in warnings()[0]
                assert "120 seconds" in warnings()[0]
                assert not task.done()
                await advance(120)
                assert len(warnings()) == 1
            release.set()
            assert await task is succeeds
            assert coordinator._last_fetch_date == (date.today() if succeeds else None)
            await advance(300)
            assert len(warnings()) == int(slow)
        finally:
            release.set()
            await task
            await coordinator.async_shutdown()
