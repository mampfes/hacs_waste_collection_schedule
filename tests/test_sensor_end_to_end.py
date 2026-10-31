"""Consumer and concurrent-edit contracts across the complete sensor workflow."""

import asyncio
import json
from datetime import UTC, date, datetime, timedelta
from threading import Event

import pytest
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.json import json_bytes
from homeassistant.helpers.template import Template
from sensor_fixtures import entry_for
from waste_collection_schedule import Collection
from waste_collection_schedule.collection_aggregator import CollectionAggregator
from waste_collection_schedule.source_shell import Customize, SourceShell
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import GLASS, ORGANIC, PAPER

from custom_components.waste_collection_schedule.calendar import (
    calc_unique_calendar_id,
    create_calendar_entries,
)
from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.init_ui import async_migrate_entry
from custom_components.waste_collection_schedule.sensor_model import SensorConfig
from custom_components.waste_collection_schedule.sensor_options import SensorOptionsFlow


def sensor_id(ha, entry, record_id, domain="sensor", suffix=""):
    kind = "sensor" if domain == "sensor" else "control"
    return er.async_get(ha).async_get_entity_id(
        domain, DOMAIN, f"{entry.entry_id}_{kind}_{record_id}{suffix}"
    )


@pytest.mark.asyncio
async def test_dedicated_calendar_resolves_aliased_legacy_type_after_empty_fetch(ha):
    class Source:
        def __init__(self):
            self.events = []

        def fetch(self):
            return self.events

    source = Source()
    shell = SourceShell(
        source,
        {
            "Legacy paper": Customize(
                "Legacy paper", alias="Recycling", use_dedicated_calendar=True
            ),
            "Legacy glass": Customize("Legacy glass", alias="Recycling"),
        },
        "Provider",
        "Offline calendar fixture",
        None,
        "General",
        "seasonal",
        0,
    )
    assert shell.fetch()
    calendars = {
        entity.unique_id: entity for entity in create_calendar_entries([shell])
    }
    calendar = calendars[calc_unique_calendar_id(shell, "Legacy paper")]
    general = calendars[calc_unique_calendar_id(shell)]
    assert calendar.unique_id == calc_unique_calendar_id(shell, "Legacy paper")
    assert calendar.event is None
    assert general.event is None
    source.events = [
        Collection(date=date(2099, 1, 1), t="Legacy paper"),
        Collection(date=date(2099, 1, 2), t="Legacy glass"),
    ]
    assert shell.fetch()
    events = await calendar.async_get_events(
        ha, datetime(2099, 1, 1, tzinfo=UTC), datetime(2099, 1, 3, tzinfo=UTC)
    )
    assert [(event.summary, event.start) for event in events] == [
        ("Recycling", date(2099, 1, 1))
    ]
    events = await general.async_get_events(
        ha, datetime(2099, 1, 1, tzinfo=UTC), datetime(2099, 1, 3, tzinfo=UTC)
    )
    assert [(event.summary, event.start) for event in events] == [
        ("Recycling", date(2099, 1, 2))
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keys",
    [
        ("paper", "glass"),
        (PAPER.names["en"], GLASS.names["en"]),
        ("Blue bin", "Green bin"),
        ("Legacy paper", "Legacy glass"),
    ],
)
@pytest.mark.parametrize(
    "partition", ["remaining", "third", "all-dedicated", "same-day"]
)
async def test_dedicated_calendars_keep_membership_when_aliases_collide(
    ha, keys, partition
):
    class Source:
        def fetch(self):
            second_date = date(2099, 1, 1 if partition == "same-day" else 2)
            events = [
                Collection(date=date(2099, 1, 1), t=keys[0], location="Paper curb")
                if keys[0] == "Legacy paper"
                else Collection(
                    date=date(2099, 1, 1), waste_type=PAPER, location="Paper curb"
                ),
                Collection(date=second_date, t=keys[1], location="Glass depot")
                if keys[0] == "Legacy paper"
                else Collection(
                    date=second_date, waste_type=GLASS, location="Glass depot"
                ),
            ]
            for event, label in zip(events, ("Blue bin", "Green bin"), strict=True):
                event.set_original_label(label)
            if partition == "third":
                events.append(Collection(date=date(2099, 1, 3), waste_type=ORGANIC))
            return events

    shell = SourceShell(
        source=Source(),
        customize={
            keys[0]: Customize(keys[0], alias="Recycling", use_dedicated_calendar=True),
            keys[1]: Customize(
                keys[1],
                alias="Recycling",
                use_dedicated_calendar=partition == "all-dedicated",
            ),
        },
        title="Provider",
        description="Offline calendar fixture",
        url=None,
        calendar_title="General",
        unique_id="calendar-fixture",
        day_offset=0,
        ignore_duplicates=True,
    )
    assert shell.fetch()
    calendars = {
        entity.unique_id: entity for entity in create_calendar_entries([shell])
    }
    start = datetime(2099, 1, 1, tzinfo=UTC)
    end = datetime(2099, 1, 4, tzinfo=UTC)
    dedicated = calendars[calc_unique_calendar_id(shell, keys[0])]
    assert [
        event.start for event in await dedicated.async_get_events(ha, start, end)
    ] == [date(2099, 1, 1)]
    assert dedicated.event.location == "Paper curb"
    if partition == "all-dedicated":
        other = calendars[calc_unique_calendar_id(shell, keys[1])]
        assert [
            event.start for event in await other.async_get_events(ha, start, end)
        ] == [date(2099, 1, 2)]
        assert calc_unique_calendar_id(shell) not in calendars
    else:
        general = calendars[calc_unique_calendar_id(shell)]
        assert [
            event.start for event in await general.async_get_events(ha, start, end)
        ] == (
            [date(2099, 1, 2), date(2099, 1, 3)]
            if partition == "third"
            else [date(2099, 1, 1 if partition == "same-day" else 2)]
        )
        assert general.event.location == "Glass depot"


@pytest.mark.asyncio
async def test_generic_upcoming_keeps_jinja_objects_and_sensor_local_json(
    running_entry, ha
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = entry.options["sensors"][0]
    await manager.async_update(
        record["id"], {"details_format": "generic", "color": "#123456"}
    )
    await ha.async_block_till_done()
    eid = sensor_id(ha, entry, record["id"])
    event = ha.states.get(eid).attributes["upcoming"][0]
    rendered = Template(
        "{{ state_attr('" + eid + "', 'upcoming')[0].date.strftime('%d/%m/%Y') }}", ha
    ).async_render()
    assert rendered == "01/01/2099"
    days = Template(
        "{{ state_attr('" + eid + "', 'upcoming')[0].daysTo }}", ha
    ).async_render()
    assert int(days) == (date(2099, 1, 1) - date.today()).days
    serialized = json.loads(json_bytes(event))
    assert (
        serialized["date"],
        serialized["type_id"],
        serialized["color"],
        serialized["color_source"],
    ) == ("2099-01-01", "paper", "#123456", "sensor")
    assert manager.coordinator.shell._entries[0].color != "#123456"


@pytest.mark.parametrize("ignore_duplicates", [False, True])
def test_unique_bin_keeps_all_categories_of_its_earliest_combined_round(
    ignore_duplicates,
):
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={"Shared bin": [PAPER, GLASS]},
        carry_raw_label=True,
    )

    class Source:
        def fetch(self):
            return [
                entry
                for day in ("2099-01-02", "2099-01-01")
                for entry in transform({"date": day, "type": "Shared bin"})
            ]

    shell = SourceShell(
        Source(),
        {},
        "Fixture",
        "Bins",
        None,
        None,
        "fixture",
        0,
        ignore_duplicates=ignore_duplicates,
    )
    shell.fetch()
    agg = CollectionAggregator([shell])
    entries = agg.get_upcoming(unique_types=True, preserve_bins=True)
    assert [(e.date, e.waste_type.id) for e in entries] == [
        (date(2099, 1, 1), "paper"),
        (date(2099, 1, 1), "glass"),
    ]
    group = agg.get_upcoming_group_by_day(unique_types=True)[0]
    assert set(group.types) == {PAPER.names["en"], GLASS.names["en"]}
    assert {r["type_id"] for r in group.as_dict()["collections"]} == {"paper", "glass"}


@pytest.mark.asyncio
@pytest.mark.parametrize("surface", ["sensor", "customize"])
async def test_open_options_save_preserves_newer_native_edits_and_discovery(
    running_entry, ha, surface
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    paper = entry.options["sensors"][0]
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    if surface == "sensor":
        await flow.async_step_sensors(
            {
                "predefined": [
                    r["origin"]
                    for r in entry.options["sensors"]
                    if r["origin"] != "custom"
                ],
                "edit_sensor": paper["id"],
            }
        )
    else:
        await flow.async_step_waste_types({"types": ["paper"]})
    await manager.async_update(paper["id"], {"color": "#654321"})
    peer = next(r for r in entry.options["sensors"] if r["origin"] == "custom")
    er.async_get(ha).async_update_entity(
        sensor_id(ha, entry, peer["id"]), disabled_by=er.RegistryEntryDisabler.USER
    )
    await ha.async_block_till_done()
    extra = SensorConfig(
        name="Discovered later", origin="type:glass", types=["glass"], id="later"
    ).as_dict()
    ha.config_entries.async_update_entry(
        entry, options={**entry.options, "sensors": [*entry.options["sensors"], extra]}
    )
    await ha.async_block_till_done()
    if surface == "sensor":
        result = await flow.async_step_edit_sensor(
            {
                "name": "Edited name",
                "enabled": True,
                "state_format": paper["state_format"],
                "language": paper["language"],
                "date_format": paper["date_format"],
                "details_format": paper["details_format"],
            }
        )
    else:
        result = await flow.async_step_customize({"color": "#123456"})
    saved = {r["id"]: r for r in result["data"]["sensors"]}
    assert saved[paper["id"]]["color"] == "#654321"
    assert saved["later"] == extra
    assert saved[peer["id"]]["enabled"] is False
    if surface == "sensor":
        assert saved[paper["id"]]["name"] == "Edited name"


@pytest.mark.asyncio
async def test_open_sensor_editor_does_not_resurrect_concurrently_deleted_record(
    running_entry, ha
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = next(r for r in entry.options["sensors"] if r["origin"] == "custom")
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    await flow.async_step_sensors({"predefined": [], "edit_sensor": record["id"]})
    await manager.async_delete(record["id"])
    await ha.async_block_till_done()
    result = await flow.async_step_edit_sensor({"name": "Stale edit"})
    assert not any(
        r["id"] == record["id"] for r in result.get("data", {}).get("sensors", [])
    )
    assert result["type"] == "abort"


@pytest.mark.asyncio
async def test_reset_in_open_editor_keeps_a_new_registry_disable(running_entry, ha):
    entry, _ = running_entry
    record = entry.options["sensors"][0]
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    await flow.async_step_sensors(
        {
            "predefined": [
                r["origin"] for r in entry.options["sensors"] if r["origin"] != "custom"
            ],
            "edit_sensor": record["id"],
        }
    )
    er.async_get(ha).async_update_entity(
        sensor_id(ha, entry, record["id"]), disabled_by=er.RegistryEntryDisabler.USER
    )
    await ha.async_block_till_done()
    result = await flow.async_step_edit_sensor({"action": "reset"})
    assert (
        next(r for r in result["data"]["sensors"] if r["id"] == record["id"])["enabled"]
        is False
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_entry",
    [
        {
            "device_controls": True,
            "records": [
                {
                    "id": "long",
                    "name": "Long template",
                    "origin": "custom",
                    "advanced": True,
                    "types": ["paper"],
                }
            ],
        }
    ],
    indirect=True,
)
async def test_long_saved_template_is_preserved_and_native_control_recovers(
    running_entry, ha
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = entry.options["sensors"][0]
    template = "{#" + "long comment " * 40 + "#}{{ value.daysTo }}"
    await manager.async_update(
        record["id"],
        {"advanced": True, "state_format": "custom", "value_template": template},
    )
    await ha.async_block_till_done()
    eid = sensor_id(ha, entry, record["id"], "text", "_value_template")
    state = ha.states.get(eid)
    assert state is not None and state.state == "unavailable"
    assert (
        next(r for r in entry.options["sensors"] if r["id"] == record["id"])[
            "value_template"
        ]
        == template
    )
    await manager.async_update(record["id"], {"value_template": "{{ value.daysTo }}"})
    await ha.async_block_till_done()
    assert ha.states.get(eid).state == "{{ value.daysTo }}"


@pytest.mark.asyncio
@pytest.mark.parametrize("trigger", ["reload", "re-enable", "controls"])
@pytest.mark.parametrize("fetch_state", ["fresh", "due-success", "due-failure"])
async def test_cached_reload_retries_due_fetch_without_losing_sensors(
    running_entry, ha, trigger, fetch_state
):
    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    last_fetch = date.today() - timedelta(days=2 if fetch_state != "fresh" else 0)
    coordinator._last_fetch_date = last_fetch
    eid = sensor_id(ha, entry, "type_paper")
    assert ha.states.get(eid).attributes["date"] == "2099-01-01"

    def fetch():
        source.fetch_count += 1
        if fetch_state == "due-failure":
            raise RuntimeError("Synthetic provider outage")
        return [Collection(date=date(2099, 1, 2), waste_type=PAPER)]

    source.fetch = fetch
    if trigger == "reload":
        assert await ha.config_entries.async_reload(entry.entry_id)
    elif trigger == "re-enable":
        await ha.config_entries.async_set_disabled_by(
            entry.entry_id, ConfigEntryDisabler.USER
        )
        await ha.config_entries.async_set_disabled_by(entry.entry_id, None)
    else:
        ha.config_entries.async_update_entry(
            entry, options={**entry.options, "device_controls": True}
        )
    await ha.async_block_till_done(wait_background_tasks=True)
    assert source.fetch_count == (1 if fetch_state == "fresh" else 2)
    assert entry.state.value == "loaded"
    current = ha.data[DOMAIN][entry.entry_id]
    assert sensor_id(ha, entry, "type_paper") == eid
    assert ha.states.get(eid).attributes["date"] == (
        "2099-01-02" if fetch_state == "due-success" else "2099-01-01"
    )
    assert current._last_fetch_date == (
        date.today() if fetch_state == "due-success" else last_fetch
    )
    assert current._fetch_tracker is not None
    if fetch_state == "due-failure":
        assert await current._fetch_now() is False
        assert source.fetch_count == 3


@pytest.mark.asyncio
async def test_due_reload_fetch_does_not_block_setup_and_is_cancelled_on_unload(
    running_entry, ha
):
    entry, source = running_entry
    ha.data[DOMAIN][entry.entry_id]._last_fetch_date = date.today() - timedelta(days=2)
    eid = sensor_id(ha, entry, "type_paper")
    started = asyncio.Event()
    release = Event()

    def fetch():
        source.fetch_count += 1
        ha.loop.call_soon_threadsafe(started.set)
        if not release.wait(10):
            raise TimeoutError("Test did not release provider")
        return [Collection(date=date(2099, 1, 2), waste_type=PAPER)]

    source.fetch = fetch
    try:
        assert await asyncio.wait_for(ha.config_entries.async_reload(entry.entry_id), 5)
        await asyncio.wait_for(started.wait(), 5)
        current = ha.data[DOMAIN][entry.entry_id]
        assert ha.states.get(eid).attributes["date"] == "2099-01-01"
        assert source.fetch_count == 2
        assert await ha.config_entries.async_unload(entry.entry_id)
    finally:
        release.set()
        await ha.async_block_till_done(wait_background_tasks=True)
    # An unloaded background fetch cannot advance the old coordinator's state.
    assert current._last_fetch_date == date.today() - timedelta(days=2)
    assert current._fetch_tracker is None
    assert ha.states.get(eid).state == "unavailable"


@pytest.mark.asyncio
async def test_repeated_reload_serializes_surviving_provider_workers(running_entry, ha):
    entry, source = running_entry
    ha.data[DOMAIN][entry.entry_id]._last_fetch_date = date.today() - timedelta(days=2)
    started = asyncio.Event()
    overlap = asyncio.Event()
    release = Event()

    def fetch():
        source.fetch_count += 1
        if source.fetch_count == 2:
            ha.loop.call_soon_threadsafe(started.set)
            if not release.wait(10):
                raise TimeoutError("Test did not release first provider worker")
            return [Collection(date=date(2099, 1, 2), waste_type=PAPER)]
        ha.loop.call_soon_threadsafe(overlap.set)
        return [Collection(date=date(2099, 1, 3), waste_type=PAPER)]

    source.fetch = fetch
    try:
        assert await ha.config_entries.async_reload(entry.entry_id)
        await asyncio.wait_for(started.wait(), 5)
        assert await ha.config_entries.async_reload(entry.entry_id)
        # The first worker survives coroutine cancellation. Its replacement must
        # wait for that worker rather than issuing an overlapping provider call.
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(overlap.wait(), 0.1)
    finally:
        release.set()
        await ha.async_block_till_done(wait_background_tasks=True)
    current = ha.data[DOMAIN][entry.entry_id]
    assert source.fetch_count == 3
    eid = sensor_id(ha, entry, "type_paper")
    assert ha.states.get(eid).attributes["date"] == "2099-01-03"
    assert current._aggregator.get_upcoming()[0].date == date(2099, 1, 3)
    assert current._last_fetch_date == date.today()


@pytest.mark.asyncio
async def test_fetch_service_does_not_request_disabled_entries(running_entry, ha):
    entry, source = running_entry
    ha.data[DOMAIN][entry.entry_id]._last_fetch_date = date.today() - timedelta(days=2)
    await ha.config_entries.async_set_disabled_by(
        entry.entry_id, ConfigEntryDisabler.USER
    )
    await ha.services.async_call(DOMAIN, "fetch_data", {}, blocking=True)
    await ha.async_block_till_done(wait_background_tasks=True)
    assert source.fetch_count == 1
    await ha.config_entries.async_set_disabled_by(entry.entry_id, None)
    await ha.async_block_till_done(wait_background_tasks=True)
    assert source.fetch_count == 2
    assert entry.state.value == "loaded"
    await ha.services.async_call(DOMAIN, "fetch_data", {}, blocking=True)
    await ha.async_block_till_done(wait_background_tasks=True)
    assert source.fetch_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keys", [(PAPER.names["en"], PAPER.names["fr"]), (PAPER.names["en"], "paper")]
)
async def test_customize_migration_collision_keeps_settings_and_calendar_ids(ha, keys):
    custom = {
        k: {"alias": f"Bin {i}", "color": color, "use_dedicated_calendar": True}
        for i, (k, color) in enumerate(zip(keys, ("#123456", "#654321"), strict=True))
    }
    entry = entry_for(ha, {"sensors": [], "customize": custom}, version=3)
    registry = er.async_get(ha)
    before = [
        registry.async_get_or_create(
            "calendar", DOMAIN, f"{entry.entry_id}_{k}_calendar", config_entry=entry
        ).entity_id
        for k in keys
    ]
    assert await async_migrate_entry(ha, entry)
    assert dict(entry.options["customize"]) == custom
    assert [
        registry.async_get_entity_id(
            "calendar", DOMAIN, f"{entry.entry_id}_{k}_calendar"
        )
        for k in keys
    ] == before


@pytest.mark.asyncio
@pytest.mark.parametrize("details", ["appointment_types", "generic"])
@pytest.mark.parametrize("included", [[], ["paper", "glass"]])
async def test_excluded_type_is_absent_from_detail_type_lists(
    running_entry, ha, details, included
):
    entry, source = running_entry
    source.types = [PAPER, GLASS]
    coordinator = ha.data[DOMAIN][entry.entry_id]
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    record = next(r for r in entry.options["sensors"] if r["origin"] == "custom")
    await coordinator.sensor_manager.async_update(
        record["id"],
        {"types": included, "exclude_types": ["glass"], "details_format": details},
    )
    await ha.async_block_till_done()
    attrs = ha.states.get(sensor_id(ha, entry, record["id"])).attributes
    assert GLASS.names["en"] not in (
        attrs if details == "appointment_types" else attrs["types"]
    )
    assert PAPER.names["en"] in (
        attrs if details == "appointment_types" else attrs["types"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [None, 1])
async def test_generic_pickup_index_skips_date_groups_before_flattening(
    running_entry, ha, count
):
    entry, source = running_entry
    source.fetch = lambda: [
        Collection(date=date(2099, 1, 1), waste_type=PAPER),
        Collection(date=date(2099, 1, 1), waste_type=GLASS),
        Collection(date=date(2099, 1, 2), waste_type=PAPER),
    ]
    coordinator = ha.data[DOMAIN][entry.entry_id]
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    record = next(r for r in entry.options["sensors"] if r["origin"] == "custom")
    await coordinator.sensor_manager.async_update(
        record["id"],
        {"types": [], "details_format": "generic", "event_index": 1, "count": count},
    )
    await ha.async_block_till_done()
    attrs = ha.states.get(sensor_id(ha, entry, record["id"])).attributes
    assert attrs["date"] == "2099-01-02"
    assert [(e.date, e.waste_type.id) for e in attrs["upcoming"]] == [
        (date(2099, 1, 2), "paper")
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_entry", [{"records": [], "types": [PAPER, GLASS]}], indirect=True
)
async def test_enabling_discovery_immediately_uses_the_cached_schedule(
    running_entry, ha
):
    entry, source = running_entry
    assert not entry.options["sensors"]
    ha.config_entries.async_update_entry(
        entry, options={**entry.options, "auto_add_types": True}
    )
    await ha.async_block_till_done()
    assert {r["origin"] for r in entry.options["sensors"]} == {
        "type:paper",
        "type:glass",
    }
    assert all(sensor_id(ha, entry, r["id"]) for r in entry.options["sensors"])
    assert source.fetch_count == 1
