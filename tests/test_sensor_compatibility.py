"""Legacy configuration and native HA compatibility regressions."""

from datetime import date

import pytest
from homeassistant.helpers import entity_registry as er
from waste_collection_schedule import Collection
from waste_collection_schedule.waste_types import PAPER

from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.sensor_options import SensorOptionsFlow


@pytest.mark.asyncio
@pytest.mark.parametrize("details", ["appointment_types", "generic"])
@pytest.mark.parametrize(
    "running_entry",
    [
        {
            "types": [Collection(date=date(2099, 1, 1), t="paper").waste_type],
            "records": [
                {
                    "id": "raw",
                    "name": "Raw paper",
                    "origin": "custom",
                    "types": ["paper"],
                }
            ],
            "options": {"customize": {"paper": {"use_dedicated_calendar": True}}},
        }
    ],
    indirect=True,
)
async def test_raw_label_matching_canonical_id_keeps_calendar_and_detail_output(
    running_entry, ha, details
):
    from custom_components.waste_collection_schedule.calendar import (
        create_calendar_entries,
    )

    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    calendar = next(
        c
        for c in create_calendar_entries([coordinator.shell], coordinator=coordinator)
        if c.unique_id == entry.entry_id + "_paper_calendar"
    )
    assert calendar.event is not None
    assert calendar.event.summary == "paper"
    await coordinator.sensor_manager.async_update("raw", {"details_format": details})
    await ha.async_block_till_done()
    eid = er.async_get(ha).async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_raw"
    )
    attrs = ha.states.get(eid).attributes
    assert (
        attrs["paper"] == "2099-01-01"
        if details == "appointment_types"
        else attrs["types"] == ["paper"]
    )
    source.types = []
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    await ha.async_block_till_done()
    attrs = ha.states.get(eid).attributes
    assert (
        attrs["paper"] == ""
        if details == "appointment_types"
        else attrs["types"] == ["paper"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_entry,template_key",
    [
        (
            {
                "records": [
                    {
                        "name": "Broken",
                        "id": "broken",
                        "origin": "custom",
                        "types": ["paper"],
                        key: "{% if %}",
                    },
                    {
                        "name": "Working",
                        "id": "working",
                        "origin": "custom",
                        "types": ["paper"],
                    },
                ]
            },
            key,
        )
        for key in ("value_template", "date_template")
    ],
    indirect=["running_entry"],
)
async def test_invalid_stored_template_isolated_and_recovers(
    running_entry, ha, caplog, template_key
):
    entry, source = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    registry = er.async_get(ha)
    broken = registry.async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_broken"
    )
    working = registry.async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_working"
    )
    assert ha.states.get(broken).state == "unavailable"
    assert ha.states.get(working).state != "unavailable"
    assert any(
        f"Invalid {template_key}" in r.getMessage() for r in caplog.get_records("setup")
    )
    await manager.async_update(
        "broken",
        {
            "value_template": None,
            "date_template": None,
            template_key: "{{ value.daysTo }}",
        },
    )
    await ha.async_block_till_done()
    assert ha.states.get(broken).state not in ("unknown", "unavailable")
    assert (
        registry.async_get_entity_id(
            "sensor", DOMAIN, entry.entry_id + "_sensor_broken"
        )
        == broken
    )
    assert source.fetch_count == 1


@pytest.mark.asyncio
async def test_legacy_negative_limits_do_not_block_migration(ha, caplog):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule.init_ui import async_migrate_entry

    entry = entry_for(
        ha,
        {
            "sensors": [
                {"name": "Old limits", "leadtime": -1, "event_index": -2, "count": 0}
            ]
        },
        version=3,
    )
    assert await async_migrate_entry(ha, entry)
    r = entry.options["sensors"][0]
    assert (r["leadtime"], r["event_index"], r["count"]) == (0, 0, None)
    assert "Old limits" in caplog.text and "negative legacy limits" in caplog.text


@pytest.mark.asyncio
async def test_customize_key_migration_retains_dedicated_calendar_registry_identity(ha):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule.init_ui import async_migrate_entry

    entry = entry_for(
        ha,
        {
            "customize": {
                PAPER.names["en"]: {"alias": "Blue bin", "use_dedicated_calendar": True}
            },
            "sensors": [],
        },
        version=3,
    )
    registry = er.async_get(ha)
    old = registry.async_get_or_create(
        "calendar",
        DOMAIN,
        f"{entry.entry_id}_{PAPER.names['en']}_calendar",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    registry.async_update_entity(old.entity_id, name="Calendar override")
    assert await async_migrate_entry(ha, entry)
    migrated = registry.async_get(old.entity_id)
    assert migrated.unique_id == entry.entry_id + "_paper_calendar"
    assert migrated.name == "Calendar override"
    assert migrated.disabled_by == er.RegistryEntryDisabler.USER
    assert entry.options["customize"]["paper"]["use_dedicated_calendar"]


@pytest.mark.asyncio
@pytest.mark.parametrize("details", ["appointment_types", "generic"])
@pytest.mark.parametrize(
    "running_entry",
    [
        {
            "version": 3,
            "options": {"customize": {"paper": {"alias": "Blue bin"}}},
            "records": [
                {
                    "name": "Old paper",
                    "types": ["Blue bin"],
                    "details_format": "appointment_types",
                }
            ],
        }
    ],
    indirect=True,
)
async def test_type_id_filters_keep_display_labels_in_legacy_details(
    running_entry, ha, details
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = entry.options["sensors"][0]
    await manager.async_update(record["id"], {"details_format": details})
    await ha.async_block_till_done()
    eid = er.async_get(ha).async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_" + record["id"]
    )
    attrs = ha.states.get(eid).attributes
    if details == "appointment_types":
        assert attrs["Blue bin"] == "2099-01-01"
        assert "paper" not in attrs
    else:
        assert attrs["types"] == ["Blue bin"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_entry",
    [
        {
            "device_controls": True,
            "records": [
                {
                    "name": "Paper",
                    "id": "paper",
                    "origin": "custom",
                    "types": ["paper"],
                },
                {
                    "name": "Paper bin",
                    "id": "paper_bin",
                    "origin": "custom",
                    "types": ["paper"],
                },
            ],
        }
    ],
    indirect=True,
)
async def test_control_registry_uses_exact_sensor_id_with_shared_prefix(
    running_entry, ha
):
    entry, _ = running_entry
    registry = er.async_get(ha)
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    uid = entry.entry_id + "_control_paper_bin_name"
    eid = registry.async_get_entity_id("text", DOMAIN, uid)
    assert eid is not None
    await manager.async_update("paper", {"name": "Renamed first"})
    await ha.async_block_till_done()
    assert registry.async_get_entity_id("text", DOMAIN, uid) == eid
    assert ha.states.get(eid).state == "Paper bin"


@pytest.mark.asyncio
async def test_omitted_cleared_optional_fields_remove_saved_overrides(
    running_entry, ha
):
    entry, _ = running_entry
    manager = ha.data[DOMAIN][entry.entry_id].sensor_manager
    record = entry.options["sensors"][0]
    await manager.async_update(
        record["id"],
        {
            "color": "#ABCDEF",
            "value_template": "{{ value.daysTo }}",
            "date_template": "{{ value.date }}",
        },
    )
    await ha.async_block_till_done()
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    enabled = [
        r["origin"]
        for r in entry.options["sensors"]
        if r["origin"] != "custom" and r["enabled"]
    ]
    await flow.async_step_sensors({"predefined": enabled, "edit_sensor": record["id"]})
    await flow.async_step_edit_sensor(
        {"name": record["name"], "enabled": True, "advanced": True}
    )
    form = await flow.async_step_sensor_advanced()
    saved = await flow.async_step_sensor_advanced(
        form["data_schema"]({"event_index": 0})
    )
    result = next(r for r in saved["data"]["sensors"] if r["id"] == record["id"])
    assert (result["color"], result["value_template"], result["date_template"]) == (
        None,
        None,
        None,
    )


def test_iso_date_rendering_does_not_load_babel_locale(monkeypatch):
    from custom_components.waste_collection_schedule import sensor_format

    def reject(*args, **kwargs):
        raise AssertionError("ISO should not invoke Babel")

    monkeypatch.setattr(sensor_format, "format_date", reject)
    assert sensor_format.render_date(date(2099, 1, 1), "iso", "de") == "2099-01-01"


@pytest.mark.asyncio
async def test_rich_schedule_uses_recorder_exclusions_without_truncation(
    running_entry, ha
):
    import json
    from datetime import timedelta

    from waste_collection_schedule import Collection

    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]

    def fetch():
        return [
            Collection(date=date(2099, 1, 1) + timedelta(days=n), waste_type=PAPER)
            for n in range(100)
        ]

    source.fetch = fetch
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    await ha.async_block_till_done()
    eid = er.async_get(ha).async_get_entity_id(
        "sensor", DOMAIN, entry.entry_id + "_sensor_type_paper"
    )
    state = ha.states.get(eid)
    assert len(state.attributes["upcoming"]) == 100
    assert len(json.dumps(state.attributes["upcoming"])) > 16384
    assert {"upcoming", "collections"} <= state.state_info["unrecorded_attributes"]
    assert state.attributes["date"] == "2099-01-01"


@pytest.mark.asyncio
async def test_locale_data_is_prepared_in_executor_for_native_options(
    running_entry, ha, monkeypatch
):
    import threading

    from custom_components.waste_collection_schedule import sensor_format
    from custom_components.waste_collection_schedule.sensor_model import LANGUAGES

    entry, _ = running_entry
    main_thread = threading.get_ident()
    calls = []
    original = sensor_format.format_date

    def capture(*args, **kwargs):
        calls.append((kwargs["locale"], threading.get_ident()))
        return original(*args, **kwargs)

    sensor_format._prepare_locales.cache_clear()
    monkeypatch.setattr(sensor_format, "format_date", capture)
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    await flow.async_step_init()
    assert {lang for lang, _ in calls} == set(LANGUAGES) - {"auto"}
    assert all(thread != main_thread for _, thread in calls)


@pytest.mark.asyncio
async def test_source_title_and_customize_overrides_can_be_cleared(running_entry, ha):
    entry, _ = running_entry
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    form = await flow.async_step_source_settings()
    title = next(k for k in form["data_schema"].schema if str(k) == "calendar_title")
    assert title.description["suggested_value"] is None
    ha.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            "calendar_title": "Old title",
            "customize": {"paper": {"alias": "Old alias", "color": "#123456"}},
        },
    )
    await ha.async_block_till_done()
    form = await flow.async_step_source_settings()
    saved = await flow.async_step_source_settings(form["data_schema"]({}))
    assert "calendar_title" not in saved["data"]
    await flow.async_step_waste_types({"types": ["paper"]})
    form = await flow.async_step_customize()
    saved = await flow.async_step_customize(form["data_schema"]({"show": True}))
    assert "alias" not in saved["data"]["customize"]["paper"]
    assert "color" not in saved["data"]["customize"]["paper"]


def test_generated_common_translations_cover_project_language_contract():
    import json
    from pathlib import Path

    from custom_components.waste_collection_schedule.sensor_model import LANGUAGES
    from sensor_translation_labels import COMMON_LABELS
    from sensor_translations import FIELD_LABELS, MENUS, apply_sensor_translations

    paths = list(
        (
            Path(__file__).parents[1]
            / "custom_components/waste_collection_schedule/translations"
        ).glob("*.json")
    )
    project_languages = {p.stem for p in paths}
    assert set(LANGUAGES) - {"auto"} == project_languages
    for path in paths:
        assert (
            path.stem in FIELD_LABELS
            and path.stem in MENUS
            and path.stem in COMMON_LABELS
        )
        content = json.loads(path.read_text())
        apply_sensor_translations(content, path.stem)
        assert "pl" not in content["selector"]["language"]["options"]
        assert content["entity"]["button"]["create_sensor"]["name"].count("{name}") == 1
        assert (
            content["issues"]["legacy_sensors"]["description"].count("{entities}") == 1
        )
        assert content["exceptions"]["type_unavailable"]["message"]
        json.dumps(content)
