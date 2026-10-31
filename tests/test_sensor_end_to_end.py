"""Consumer and concurrent-edit contracts across the complete sensor workflow."""

import json
from datetime import date, timedelta

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.json import json_bytes
from homeassistant.helpers.template import Template
from sensor_fixtures import entry_for
from waste_collection_schedule import Collection
from waste_collection_schedule.collection_aggregator import CollectionAggregator
from waste_collection_schedule.source_shell import SourceShell
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import GLASS, PAPER

from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.init_ui import async_migrate_entry
from custom_components.waste_collection_schedule.sensor_migration import migrate_records
from custom_components.waste_collection_schedule.sensor_model import SensorConfig
from custom_components.waste_collection_schedule.sensor_options import SensorOptionsFlow


def sensor_id(ha, entry, record_id, domain="sensor", suffix=""):
    kind = "sensor" if domain == "sensor" else "control"
    return er.async_get(ha).async_get_entity_id(
        domain, DOMAIN, f"{entry.entry_id}_{kind}_{record_id}{suffix}"
    )


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
async def test_due_display_reload_reuses_schedule_while_provider_is_down(
    running_entry, ha
):
    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    coordinator._last_fetch_date = date.today() - timedelta(days=2)

    def fail():
        source.fetch_count += 1
        raise RuntimeError("Synthetic provider outage")

    source.fetch = fail
    ha.config_entries.async_update_entry(
        entry, options={**entry.options, "device_controls": True}
    )
    await ha.async_block_till_done()
    assert source.fetch_count == 1
    assert entry.state.value == "loaded"
    current = ha.data[DOMAIN][entry.entry_id]
    assert current._last_fetch_date == date.today() - timedelta(days=2)
    assert current._fetch_tracker is not None
    assert await current._fetch_now() is False
    assert source.fetch_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("days", [0, 1, 3])
@pytest.mark.parametrize(
    "language,expected",
    [
        ("de", ("Paper heute", "Paper morgen", "Paper in 3 Tagen")),
        ("pl", ("Paper dzisiaj", "Paper jutro", "Paper za 3 dni")),
    ],
)
async def test_preview_default_language_retains_exact_text(
    ha, language, expected, days
):
    from waste_collection_schedule.collection import CollectionGroup

    record = migrate_records(
        {"sensors": [{"name": "Preview", "preset_language": language}]}
    )["sensors"][0]
    group = CollectionGroup.create(
        [Collection(date=date.today() + timedelta(days=days), waste_type=PAPER)]
    )
    result = Template(
        record["value_template"], ha
    ).async_render_with_possible_json_value(group, None)
    assert result == expected[(0, 1, 3).index(days)].replace("Paper", PAPER.names["en"])


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
