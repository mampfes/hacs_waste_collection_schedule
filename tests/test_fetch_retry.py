import asyncio
import os
import sys
from datetime import date, timedelta
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
from waste_collection_schedule.waste_types import PAPER  # isort:skip


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
    unsubs = [Mock() for _ in range(5)]
    (
        coordinator._fetch_tracker,
        coordinator._day_switch_tracker,
        coordinator._midnight_tracker,
        coordinator._fetch_later_unsub,
        coordinator._retry_unsub,
    ) = unsubs

    coordinator._async_unsub_timers()

    for unsub in unsubs:
        unsub.assert_called_once_with()
    assert coordinator._fetch_tracker is None
    assert coordinator._day_switch_tracker is None
    assert coordinator._midnight_tracker is None
    assert coordinator._fetch_later_unsub is None
    assert coordinator._retry_unsub is None


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


@pytest.mark.asyncio
async def test_cache_restores_entries_only_for_the_same_source_and_options(ha):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule import wcs_coordinator

    class _Source:
        def fetch(self):
            # two bins of one type on one day: the calendar merges them
            bins = []
            for label in ("Small bin", "Large bin"):
                bins.append(Collection(date=date(2099, 1, 1), waste_type=PAPER))
                bins[-1].set_original_label(label)
            bins[0].set_source_color("#123456")
            return [*bins, Collection(date=date(2099, 1, 8), t="Glass")]

    entry = entry_for(ha, {})
    data = {"name": "test", "args": {"street": "a", "password": "hunter2"}}
    ha.config_entries.async_update_entry(entry, data=data)
    source = _Source()

    def coordinator():
        shell = SourceShell(
            source, {}, "Test", "Test", None, None, "cache", 0, ignore_duplicates=True
        )
        return wcs_coordinator.WCSCoordinator(
            ha, entry, shell, ", ", "01:00", 1, 0, "10:00"
        )

    first = coordinator()
    assert await first._fetch_now()
    cache_file = ha.config.path(
        ".storage", f"waste_collection_schedule.cache.{entry.entry_id}"
    )
    with open(cache_file) as f:
        assert "hunter2" not in f.read()

    restarted = coordinator()
    assert await restarted.async_restore_cache()
    for attr in ("_entries", "_sensor_entries"):
        restored, fetched = getattr(restarted.shell, attr), getattr(first.shell, attr)
        assert restored == fetched
        assert [e.as_dict() for e in restored] == [e.as_dict() for e in fetched]
    assert len(restarted.shell._sensor_entries) > len(restarted.shell._entries)
    assert restarted.shell.raw_labels == ["Large bin", "Small bin"]
    assert restarted.shell.refreshtime == first.shell.refreshtime

    # malformed or incomplete payloads fall back to fetching
    store = wcs_coordinator.cache_store(ha, entry.entry_id)
    cached = await store.async_load()
    for broken in (["x"], {k: v for k, v in cached.items() if k != "raw_labels"}):
        await store.async_save(broken)
        assert not await coordinator().async_restore_cache()
    await store.async_save(cached)

    # the key covers exactly the source args and options that shape the entries
    def key(entry_data=data, **options):
        ha.config_entries.async_update_entry(entry, data=entry_data, options=options)
        return coordinator()._cache_key

    base = key()
    assert key({**data, "args": {"street": "x"}}) != base
    reordered = {"args": dict(reversed(data["args"].items())), "name": "test"}
    assert key(reordered) == base
    assert key(day_offset=1) != key()
    rules = {"Pa*": {"alias": "A"}, "P*": {"alias": "B"}}
    forward = key(customize=rules)
    key()  # HA ignores an update that only reorders a dict
    assert key(customize=dict(reversed(rules.items()))) != forward
    key()
    assert await coordinator().async_restore_cache()

    # a fetch that outlives a reconfigure keeps the key it was started with
    running = coordinator()
    ha.config_entries.async_update_entry(entry, data={**data, "args": {"street": "x"}})
    assert await running._fetch_now()
    assert not await coordinator().async_restore_cache()

    # a cache with only past dates must not hide a broken setup
    ha.config_entries.async_update_entry(entry, data=data)
    stale = coordinator()
    source.fetch = lambda: [Collection(date=date(2000, 1, 1), t="Old")]
    assert await stale._fetch_now()
    assert not await coordinator().async_restore_cache()

    for c in (first, restarted, running, stale):
        await c.async_shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("cached", [True, False])
async def test_restart_with_a_provider_that_never_answers_does_not_block_setup(
    running_entry, ha, monkeypatch, cached
):
    from homeassistant.config_entries import ConfigEntryState

    from custom_components.waste_collection_schedule import init_ui, wcs_coordinator
    from custom_components.waste_collection_schedule.const import DOMAIN

    entry, source = running_entry
    shell = ha.data[DOMAIN][entry.entry_id].shell
    assert await ha.config_entries.async_unload(entry.entry_id)
    # simulate a restart: no previous coordinator and no entries in memory
    ha.data[DOMAIN].pop(entry.entry_id)
    shell._entries = []
    if not cached:
        await wcs_coordinator.cache_store(ha, entry.entry_id).async_remove()

    release = Event()
    paper = Collection(date=date(2099, 1, 1), waste_type=PAPER)
    monkeypatch.setattr(source, "fetch", lambda: release.wait(10) and [paper])
    monkeypatch.setattr(init_ui, "FIRST_FETCH_TIMEOUT", 0.1)
    try:
        async with asyncio.timeout(5):
            assert await ha.config_entries.async_setup(entry.entry_id) is cached
        if cached:
            assert entry.state is ConfigEntryState.LOADED
            assert [e.date for e in shell._entries] == [date(2099, 1, 1)]
        else:
            assert entry.state is ConfigEntryState.SETUP_RETRY
            # the fetch outlives the timeout and fills the cache for the retry
            release.set()
            async with asyncio.timeout(5):
                while not await wcs_coordinator.cache_store(
                    ha, entry.entry_id
                ).async_load():
                    await asyncio.sleep(0.01)
    finally:
        release.set()
        await ha.async_block_till_done()


@pytest.mark.asyncio
async def test_fetch_with_retry_backs_off_until_a_fetch_succeeds(ha, monkeypatch):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule import wcs_coordinator

    class _Source:
        failures = 4

        def fetch(self):
            self.failures -= 1
            if self.failures >= 0:
                raise RuntimeError("Synthetic provider outage")
            return [Collection(date=date(2099, 1, 1), t="Paper")]

    delays = []
    monkeypatch.setattr(
        wcs_coordinator,
        "async_call_later",
        lambda _hass, delay, _action: delays.append(delay) or Mock(),
    )
    shell = SourceShell(_Source(), {}, "Test", "Test", None, None, "retry", 0)
    coordinator = wcs_coordinator.WCSCoordinator(
        ha, entry_for(ha, {}), shell, ", ", "01:00", 1, 0, "10:00"
    )
    try:
        for _ in range(5):
            await coordinator.async_fetch_with_retry()
        retries = [d for d in delays if d != wcs_coordinator.FETCH_WARNING_SECONDS]
        assert retries == [timedelta(minutes=m) for m in (5, 15, 60, 60)]
        assert coordinator._last_fetch_date == date.today()
        assert coordinator._retry_count == 0
    finally:
        await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_removing_the_entry_deletes_its_cache(running_entry, ha):
    from custom_components.waste_collection_schedule import wcs_coordinator

    entry, _source = running_entry
    store = wcs_coordinator.cache_store(ha, entry.entry_id)
    assert await store.async_load()
    await ha.config_entries.async_remove(entry.entry_id)
    assert await store.async_load() is None


@pytest.mark.asyncio
async def test_changed_source_args_do_not_wait_for_a_hung_fetch(ha):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule import wcs_coordinator

    started, release = asyncio.Event(), Event()

    class _Hung:
        def fetch(self):
            ha.loop.call_soon_threadsafe(started.set)
            release.wait(10)
            return [Collection(date=date(2099, 1, 1), t="Old address")]

    class _Fixed:
        def fetch(self):
            return [Collection(date=date(2099, 1, 1), t="New address")]

    entry = entry_for(ha, {})

    def coordinator(source):
        shell = SourceShell(source, {}, "Test", "Test", None, None, "args", 0)
        return wcs_coordinator.WCSCoordinator(
            ha, entry, shell, ", ", "01:00", 1, 0, "10:00"
        )

    old = coordinator(_Hung())
    hung = ha.async_create_task(old._fetch_now())
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        ha.config_entries.async_update_entry(entry, data={"name": "x", "args": {}})
        new = coordinator(_Fixed())
        async with asyncio.timeout(5):
            assert await new._fetch_now()
    finally:
        release.set()
        await hung
    # the old address's late result must not replace the new cache
    restarted = coordinator(_Fixed())
    assert await restarted.async_restore_cache()
    assert [e.type for e in restarted.shell._entries] == ["New address"]
    for c in (old, new, restarted):
        await c.async_shutdown()


@pytest.mark.asyncio
async def test_setup_retries_do_not_queue_fetches_behind_a_hung_one(
    running_entry, ha, monkeypatch
):
    from custom_components.waste_collection_schedule import init_ui, wcs_coordinator
    from custom_components.waste_collection_schedule.const import DOMAIN

    entry, source = running_entry
    assert await ha.config_entries.async_unload(entry.entry_id)
    ha.data[DOMAIN].pop(entry.entry_id)
    await wcs_coordinator.cache_store(ha, entry.entry_id).async_remove()

    release, calls = Event(), []
    monkeypatch.setattr(
        source, "fetch", lambda: calls.append(1) or (release.wait(10) and [])
    )
    monkeypatch.setattr(init_ui, "FIRST_FETCH_TIMEOUT", 0.1)
    try:
        for _ in range(4):
            await ha.config_entries.async_reload(entry.entry_id)
        fetches = [
            t
            for t in asyncio.all_tasks()
            if t.get_name() == "Waste collection provider fetch" and not t.done()
        ]
        assert len(fetches) == len(calls) == 1
    finally:
        release.set()
        await ha.async_block_till_done()


@pytest.mark.asyncio
@pytest.mark.parametrize("remove", [False, True])
async def test_in_progress_cache_write_is_ordered_with_reconfigure_or_removal(
    running_entry, ha, monkeypatch, remove
):
    from custom_components.waste_collection_schedule import wcs_coordinator
    from custom_components.waste_collection_schedule.const import DOMAIN

    entry, _source = running_entry
    old = ha.data[DOMAIN][entry.entry_id]
    writing, release = asyncio.Event(), asyncio.Event()
    save = old._store.async_save

    async def delayed_save(data):
        writing.set()
        await release.wait()
        await save(data)

    monkeypatch.setattr(old._store, "async_save", delayed_save)
    old._last_fetch_date = None
    fetching = ha.async_create_task(old._fetch_now())
    replacement = None
    changing = None
    try:
        await asyncio.wait_for(writing.wait(), timeout=5)
        assert await ha.config_entries.async_unload(entry.entry_id)
        if remove:
            changing = ha.async_create_task(
                ha.config_entries.async_remove(entry.entry_id)
            )
        else:
            ha.config_entries.async_update_entry(
                entry, data={**entry.data, "args": {"street": "new"}}
            )

            class Source:
                def fetch(self):
                    return [Collection(date=date(2099, 1, 1), t="New address")]

            shell = SourceShell(Source(), {}, "Test", "Test", None, None, "new", 0)
            replacement = wcs_coordinator.WCSCoordinator(
                ha, entry, shell, ", ", "01:00", 1, 0, "10:00"
            )
            changing = ha.async_create_task(replacement._fetch_now())

        # Neither operation may finish its disk work ahead of the older write.
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(asyncio.shield(changing), timeout=0.1)
        release.set()
        await fetching
        await changing

        if remove:
            assert (
                await wcs_coordinator.cache_store(ha, entry.entry_id).async_load()
                is None
            )
        else:
            assert await replacement.async_restore_cache()
            assert [e.type for e in replacement.shell._entries] == ["New address"]
    finally:
        release.set()
        await fetching
        if changing is not None:
            await changing
        if replacement is not None:
            await replacement.async_shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("past_only", [False, True])
@pytest.mark.parametrize("release_before_retry", [False, True])
async def test_setup_retry_consumes_a_slow_success_without_upcoming_collections(
    running_entry, ha, monkeypatch, past_only, release_before_retry
):
    from homeassistant.config_entries import ConfigEntryState

    from custom_components.waste_collection_schedule import init_ui, wcs_coordinator
    from custom_components.waste_collection_schedule.const import DOMAIN

    entry, source = running_entry
    assert await ha.config_entries.async_unload(entry.entry_id)
    ha.data[DOMAIN].pop(entry.entry_id)
    await wcs_coordinator.cache_store(ha, entry.entry_id).async_remove()

    release, calls = Event(), []
    result = [Collection(date=date(2000, 1, 1), t="Past")] if past_only else []

    def fetch():
        calls.append(1)
        assert release.wait(10)
        return result

    monkeypatch.setattr(source, "fetch", fetch)
    monkeypatch.setattr(init_ui, "FIRST_FETCH_TIMEOUT", 0.1)
    retry = None
    try:
        assert not await ha.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY
        workers = [
            t
            for t in asyncio.all_tasks()
            if t.get_name() == "Waste collection provider fetch" and not t.done()
        ]
        assert len(workers) == 1
        if release_before_retry:
            release.set()
            await asyncio.gather(*workers)
        monkeypatch.setattr(init_ui, "FIRST_FETCH_TIMEOUT", 1)
        retry = ha.async_create_task(ha.config_entries.async_reload(entry.entry_id))
        if not release_before_retry:
            await asyncio.sleep(0.01)
            assert not retry.done()
            release.set()
        assert await asyncio.wait_for(asyncio.shield(retry), timeout=5)
        assert entry.state is ConfigEntryState.LOADED
        assert calls == [1]
        assert ha.data[DOMAIN][entry.entry_id].shell._entries == result
        # An empty/past disk cache still cannot mask an outage on a later restart.
        assert not await ha.data[DOMAIN][entry.entry_id].async_restore_cache()
    finally:
        release.set()
        if retry is not None:
            await retry
        await ha.async_block_till_done(wait_background_tasks=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("newer_version", [False, True])
async def test_unreadable_cache_does_not_block_a_live_fetch(
    running_entry, ha, monkeypatch, newer_version
):
    from homeassistant.exceptions import HomeAssistantError
    from homeassistant.helpers.storage import Store

    from custom_components.waste_collection_schedule import wcs_coordinator
    from custom_components.waste_collection_schedule.const import DOMAIN

    entry, source = running_entry
    assert await ha.config_entries.async_unload(entry.entry_id)
    ha.data[DOMAIN].pop(entry.entry_id)
    store = wcs_coordinator.cache_store(ha, entry.entry_id)
    if newer_version:
        newer = Store(ha, wcs_coordinator.CACHE_STORAGE_VERSION + 1, store.key)
        await newer.async_save(await store.async_load())
    else:
        monkeypatch.setattr(
            store, "async_load", AsyncMock(side_effect=HomeAssistantError("Unreadable"))
        )
        monkeypatch.setattr(wcs_coordinator, "cache_store", lambda *_: store)
    calls = source.fetch_count
    assert await ha.config_entries.async_setup(entry.entry_id)
    assert source.fetch_count == calls + 1
