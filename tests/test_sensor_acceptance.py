"""Compatibility and seasonal actions through the shared real-HA boundaries."""

from datetime import date

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.collection_aggregator import CollectionAggregator
from waste_collection_schedule.source_shell import Customize, SourceShell
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    GLASS,
    PAPER,
    RECYCLABLES,
)

from custom_components.waste_collection_schedule.const import DOMAIN
from custom_components.waste_collection_schedule.default_sensors import (
    LEGACY_VALUE_TEMPLATE,
)
from custom_components.waste_collection_schedule.sensor_migration import migrate_records
from custom_components.waste_collection_schedule.sensor_options import SensorOptionsFlow


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "running_entry",
    [
        {
            "version": 3,
            "records": [
                {
                    "name": "Legacy paper",
                    "types": [PAPER.names["en"]],
                    "value_template": LEGACY_VALUE_TEMPLATE,
                    "details_format": "upcoming",
                }
            ],
        }
    ],
    indirect=True,
)
async def test_migrated_default_preserves_state_and_iso_detail_keys(running_entry, ha):
    entry, _ = running_entry
    entity_id = er.async_get(ha).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_sensor_type_paper"
    )
    state = ha.states.get(entity_id)
    assert state.state == "on Thu, 01.01.2099"
    assert state.attributes["2099-01-01"] == PAPER.names["en"]


def test_old_ui_alias_migrates_to_id_and_survives_alias_and_language_changes():
    options = {
        "customize": {PAPER.names["en"]: {"alias": "Blue bin"}},
        "sensors": [
            {
                "name": "My paper",
                "types": ["Blue bin"],
                "value_template": LEGACY_VALUE_TEMPLATE,
            }
        ],
    }
    migrated = migrate_records(options, {"paper"})
    record = migrated["sensors"][0]
    assert record["types"] == ["paper"]
    assert record["origin"] == "type:paper"
    assert migrated["customize"] == {"paper": {"alias": "Blue bin"}}

    class Source:
        def fetch(self):
            return [Collection(date=date(2099, 1, 1), waste_type=PAPER)]

    shell = SourceShell(
        source=Source(),
        customize={"paper": Customize("paper", alias="New bin name")},
        title="Fixture",
        description="Paper",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
        display_language="de",
    )
    shell.fetch()
    selected = CollectionAggregator([shell]).get_upcoming(include_types=record["types"])
    assert len(selected) == 1
    assert selected[0].type == "New bin name"


@pytest.mark.parametrize("hidden", [False, True])
def test_raw_bin_color_preserves_category_hiding_alias_and_icon(hidden):
    class Source:
        def fetch(self):
            return [
                JsonTransformer(
                    date_key="date",
                    type_key="bin",
                    type_value_map={"Small": RECYCLABLES},
                    carry_raw_label=True,
                )({"date": "2099-01-01", "bin": "Small"})
            ]

    shell = SourceShell(
        source=Source(),
        customize={
            "recyclables": Customize(
                "recyclables",
                alias="Sorted bins",
                icon=Icons.RECYCLING,
                show=not hidden,
            ),
            "Small": Customize("Small", color="#123456"),
        },
        title="Fixture",
        description="Bins",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
    )
    shell.fetch()
    if hidden:
        assert shell._entries == []
    else:
        assert shell._entries[0].type == "Sorted bins"
        assert shell._entries[0].icon == Icons.RECYCLING
        assert shell._entries[0].color == "#123456"


@pytest.mark.asyncio
async def test_options_accept_new_glob_customization_keys(running_entry, ha):
    entry, _ = running_entry
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    form = await flow.async_step_waste_types()
    submitted = form["data_schema"]({"types": ["Sonderabfall *"]})
    await flow.async_step_waste_types(submitted)
    saved = await flow.async_step_customize({"show": False})
    assert saved["data"]["customize"]["Sonderabfall *"]["show"] is False


@pytest.mark.asyncio
async def test_reset_retained_seasonal_sensor_restores_defaults(running_entry, ha):
    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    manager = coordinator.sensor_manager
    paper = next(r for r in entry.options["sensors"] if r["origin"] == "type:paper")
    await manager.async_update(
        paper["id"],
        {
            "name": "Renamed bin",
            "color": "#123456",
            "state_format": "days",
            "enabled": False,
        },
    )
    await ha.async_block_till_done()
    source.types = [GLASS]
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    await ha.async_block_till_done()
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    enabled = [
        r["origin"]
        for r in entry.options["sensors"]
        if r["origin"] != "custom" and r["enabled"]
    ]
    await flow.async_step_sensors({"predefined": enabled, "edit_sensor": paper["id"]})
    saved = await flow.async_step_edit_sensor({"action": "reset"})
    reset = next(r for r in saved["data"]["sensors"] if r["id"] == paper["id"])
    assert reset["state_format"] == "relative"
    assert reset["color"] is None
    assert reset["name"] == PAPER.names["en"]
    assert reset["enabled"] is False
    assert source.fetch_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("running_entry", [{"device_controls": True}], indirect=True)
async def test_unmaterialized_seasonal_create_button_becomes_unavailable(
    running_entry, ha
):
    entry, source = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    registry = er.async_get(ha)
    source.types = [PAPER, GLASS]
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    await ha.async_block_till_done()
    button_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_create_type_glass"
    )
    assert ha.states.get(button_id).state != "unavailable"
    assert not any(r["origin"] == "type:glass" for r in entry.options["sensors"])
    source.types = [PAPER]
    coordinator._last_fetch_date = None
    await coordinator._fetch_now()
    await ha.async_block_till_done()
    assert ha.states.get(button_id).state == "unavailable"
    assert not any(r["origin"] == "type:glass" for r in entry.options["sensors"])
    with pytest.raises(HomeAssistantError) as raised:
        await coordinator.sensor_manager.async_add_from_catalogue("type:glass")
    assert raised.value.translation_key == "type_unavailable"


@pytest.mark.parametrize("same_day", [False, True])
@pytest.mark.parametrize("aliased", [False, True])
def test_noncarried_provider_labels_remain_filterable_with_type_based_uniqueness(
    same_day,
    aliased,
):
    from waste_collection_schedule.source.ecoharmonogram_pl import Source as EcoSource

    labels = ["ODPADY ZMIESZANE", "ODPADY ZMIESZANE (2 x miesiąc)"]

    class Source:
        def fetch(self):
            return [
                EcoSource.transform(
                    {"date": f"2099-01-0{1 if same_day else index}", "type": label}
                )
                for index, label in enumerate(labels, 1)
            ]

    shell = SourceShell(
        source=Source(),
        customize={
            label: Customize(label, alias=f"Bin {index}", color=color)
            for index, (label, color) in enumerate(
                zip(labels, ("#123456", "#654321"), strict=True), 1
            )
        }
        if aliased
        else {},
        title="Fixture",
        description="Bins",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
        ignore_duplicates=True,
    )
    shell.fetch()
    aggregator = CollectionAggregator([shell])
    selected = aggregator.get_upcoming(include_types=[labels[1]])
    assert [event.date for event in selected] == [date(2099, 1, 1 if same_day else 2)]
    assert selected[0].original_label == labels[1]
    assert selected[0].description is None
    expected = 1 if same_day and not aliased else 2
    assert len(shell._entries) == expected
    assert len(aggregator.get_upcoming(preserve_bins=True)) == expected
    grouped = aggregator.get_upcoming_group_by_day()
    assert sum(len(day.as_dict()["collections"]) for day in grouped) == expected
    if aliased:
        assert {
            event.type for event in aggregator.get_upcoming(preserve_bins=True)
        } == {"Bin 1", "Bin 2"}
    assert [event.date for event in aggregator.get_upcoming(unique_types=True)] == [
        date(2099, 1, 1)
    ]


@pytest.mark.asyncio
async def test_renamed_source_migration_uses_replacement_catalogue(ha):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule.init_ui import async_migrate_entry

    entry = entry_for(
        ha,
        {
            "sensors": [
                {
                    "name": "Old paper",
                    "types": [PAPER.names["en"]],
                    "value_template": LEGACY_VALUE_TEMPLATE,
                }
            ]
        },
        version=2,
    )
    ha.config_entries.async_update_entry(
        entry,
        data={
            "name": "alw_wf_de",
            "args": {"ort": "Wolfenbüttel", "strasse": "Teststraße"},
        },
    )
    assert await async_migrate_entry(ha, entry)
    assert entry.data["name"] == "jumomind_de"
    assert entry.options["sensors"][0]["types"] == ["paper"]
    assert entry.options["sensors"][0]["origin"] == "type:paper"


@pytest.mark.asyncio
async def test_migration_collision_requires_confirmation_before_removing_legacy(ha):
    from sensor_fixtures import entry_for

    from custom_components.waste_collection_schedule.init_ui import async_migrate_entry
    from custom_components.waste_collection_schedule.repairs import (
        LegacySensorsRepairFlow,
    )

    entry = entry_for(
        ha,
        {
            "sensors": [
                {
                    "name": "Paper",
                    "types": [PAPER.names["en"]],
                    "value_template": LEGACY_VALUE_TEMPLATE,
                }
            ]
        },
        version=3,
    )
    registry = er.async_get(ha)
    legacy = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_ui_sensor_Paper", config_entry=entry
    )
    target = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_sensor_type_paper",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    assert await async_migrate_entry(ha, entry)
    assert registry.async_get(legacy.entity_id) is not None
    assert (
        registry.async_get(target.entity_id).disabled_by
        == er.RegistryEntryDisabler.USER
    )
    assert entry.options["sensors"][0]["enabled"] is False
    repair = LegacySensorsRepairFlow(entry.entry_id)
    repair.hass = ha
    prompt = await repair.async_step_init(
        {"issue_id": "legacy_sensors_" + entry.entry_id}
    )
    assert prompt["type"] == "form"
    assert registry.async_get(legacy.entity_id) is not None
    result = await repair.async_step_confirm({})
    assert result["type"] == "create_entry"
    assert registry.async_get(legacy.entity_id) is None
    assert registry.async_get(target.entity_id) is not None


@pytest.mark.asyncio
async def test_options_catalogue_uses_current_ha_display_language(running_entry, ha):
    from sensor_fixtures import entry_for

    entry, _ = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    # the running entry follows its shell's language (set from the HA UI
    # language on setup/reload)
    coordinator.shell.set_display_language("de")
    assert coordinator.sensor_manager.type_labels["paper"] == PAPER.names["de"]
    # an entry that is not running uses the current HA UI language directly
    ha.config.language = "de"
    offline = entry_for(ha, {"sensors": entry.options["sensors"]})
    flow = SensorOptionsFlow(offline)
    flow.hass = ha
    assert flow.type_labels["paper"] == PAPER.names["de"]


@pytest.mark.asyncio
async def test_reload_picks_up_a_changed_ha_display_language(running_entry, ha):
    """Setup hands hass.config.language to the entry's shell (#7025); there is
    no process-wide language, so a reload is what applies a changed one."""
    entry, _ = running_entry
    coordinator = ha.data[DOMAIN][entry.entry_id]
    assert coordinator.shell.display_language == "en"
    assert {e.type for e in coordinator.shell._entries} == {PAPER.names["en"]}
    ha.config.language = "de-DE"
    assert await ha.config_entries.async_reload(entry.entry_id)
    await ha.async_block_till_done()
    coordinator = ha.data[DOMAIN][entry.entry_id]
    assert coordinator.shell.display_language == "de"
    assert {e.type for e in coordinator.shell._entries} == {PAPER.names["de"]}
    assert coordinator.sensor_manager.type_labels["paper"] == PAPER.names["de"]


@pytest.mark.asyncio
@pytest.mark.parametrize("surface", ["setup", "options"])
async def test_customization_form_serializes_and_validates_color(
    running_entry, ha, surface
):
    from homeassistant.helpers.data_entry_flow import FlowManagerIndexView

    from custom_components.waste_collection_schedule.config_flow import (
        WasteCollectionConfigFlow,
    )

    entry, _ = running_entry
    if surface == "options":
        flow = SensorOptionsFlow(entry)
        flow.hass = ha
        await flow.async_step_waste_types({"types": ["paper"]})
    else:
        flow = WasteCollectionConfigFlow()
        flow.hass = ha
        flow._customize_types = ["paper"]
        flow._options = {}
        flow._args_data = {"name": "ecoharmonogram_pl", "args": {}}
        flow._title = "Acceptance"
    form = await flow.async_step_customize()
    serialized = FlowManagerIndexView(None)._prepare_result_json(form)
    assert any(x["name"] == "color" for x in serialized["data_schema"])
    invalid = await flow.async_step_customize({"color": "not-a-color"})
    assert invalid["type"] == "form"
    assert invalid["errors"]["base"] == "invalid_sensor"
    saved = await flow.async_step_customize({"color": "#abcdef"})
    options = saved["data"] if surface == "options" else saved["options"]
    assert options["customize"]["paper"]["color"] == "#ABCDEF"


@pytest.mark.asyncio
@pytest.mark.parametrize("surface", ["setup", "options"])
async def test_customization_form_stores_per_type_day_offset(
    running_entry, ha, surface
):
    """#7968: the per-type day_offset is optional (empty = unset), accepts
    negative values and is stored with the type's other customisation."""
    from homeassistant.helpers.data_entry_flow import FlowManagerIndexView

    from custom_components.waste_collection_schedule.config_flow import (
        WasteCollectionConfigFlow,
    )

    entry, _ = running_entry

    def start():
        if surface == "options":
            flow = SensorOptionsFlow(entry)
        else:
            flow = WasteCollectionConfigFlow()
            flow._customize_types = ["paper"]
            flow._options = {}
            flow._args_data = {"name": "ecoharmonogram_pl", "args": {}}
            flow._title = "Acceptance"
        flow.hass = ha
        return flow

    flow = start()
    if surface == "options":
        await flow.async_step_waste_types({"types": ["paper"]})
    form = await flow.async_step_customize()
    serialized = FlowManagerIndexView(None)._prepare_result_json(form)
    field = next(x for x in serialized["data_schema"] if x["name"] == "day_offset")
    assert field["optional"] is True
    assert "default" not in field
    # Left empty: nothing is stored, so the source-level offset applies.
    saved = await flow.async_step_customize(form["data_schema"]({"show": True}))
    options = saved["data"] if surface == "options" else saved["options"]
    assert "day_offset" not in options["customize"]["paper"]

    flow = start()
    if surface == "options":
        await flow.async_step_waste_types({"types": ["paper"]})
    form = await flow.async_step_customize()
    saved = await flow.async_step_customize(form["data_schema"]({"day_offset": -1}))
    options = saved["data"] if surface == "options" else saved["options"]
    assert options["customize"]["paper"]["day_offset"] == -1


@pytest.mark.asyncio
async def test_options_flow_reads_back_and_clears_per_type_day_offset(
    running_entry, ha
):
    entry, _ = running_entry
    ha.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            "customize": {"paper": {"alias": "Blue bin", "day_offset": -1}},
        },
    )
    await ha.async_block_till_done()
    flow = SensorOptionsFlow(entry)
    flow.hass = ha
    await flow.async_step_waste_types({"types": ["paper"]})
    form = await flow.async_step_customize()
    marker = next(k for k in form["data_schema"].schema if str(k) == "day_offset")
    assert marker.description["suggested_value"] == -1
    # Submitting the form with the field cleared removes the stored value.
    saved = await flow.async_step_customize(
        form["data_schema"]({"alias": "Blue bin", "show": True})
    )
    stored = saved["data"]["customize"]["paper"]
    assert stored["alias"] == "Blue bin"
    assert "day_offset" not in stored


@pytest.mark.asyncio
async def test_ui_setup_passes_per_type_day_offset_to_customize(ha):
    from unittest.mock import patch

    from sensor_fixtures import FixtureSource, entry_for

    shell = SourceShell(
        source=FixtureSource(),
        customize={},
        title="Synthetic provider",
        description="Offline fixture",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
    )
    entry = entry_for(
        ha,
        {
            "sensors": [],
            "day_offset": 2,
            "customize": {"paper": {"day_offset": -1}, "glass": {"alias": "G"}},
        },
    )
    with patch(
        "custom_components.waste_collection_schedule.init_ui.SourceShell.create",
        return_value=shell,
    ) as create:
        assert await ha.config_entries.async_setup(entry.entry_id)
        await ha.async_block_till_done()
    try:
        customize = create.call_args.args[1]
        assert customize["paper"].day_offset == -1
        assert customize["glass"].day_offset is None
        assert create.call_args.args[4] == 2  # source-level offset unchanged
    finally:
        await ha.config_entries.async_unload(entry.entry_id)
        await ha.async_block_till_done()


def test_yaml_customize_schema_accepts_per_type_day_offset():
    import voluptuous as vol

    from custom_components.waste_collection_schedule.init_yaml import (
        CUSTOMIZE_CONFIG,
        SOURCE_CONFIG,
    )

    assert CUSTOMIZE_CONFIG({"type": "Restmüll", "day_offset": -1})["day_offset"] == -1
    assert "day_offset" not in CUSTOMIZE_CONFIG({"type": "Restmüll"})
    with pytest.raises(vol.Invalid):
        CUSTOMIZE_CONFIG({"type": "Restmüll", "day_offset": "tomorrow"})
    source = SOURCE_CONFIG(
        {
            "name": "ics",
            "args": {},
            "day_offset": 1,
            "customize": [{"type": "Restmüll", "day_offset": -1}],
        }
    )
    assert source["day_offset"] == 1
    assert source["customize"][0]["day_offset"] == -1


@pytest.mark.asyncio
async def test_legacy_sensor_repair_remains_fixable_after_version4_reload(
    running_entry, ha
):
    from homeassistant.helpers import issue_registry as ir

    from custom_components.waste_collection_schedule.repairs import (
        LegacySensorsRepairFlow,
    )

    entry, _ = running_entry
    registry = er.async_get(ha)
    orphan = registry.async_get_or_create(
        "sensor", DOMAIN, entry.entry_id + "_ui_sensor_Earlier name", config_entry=entry
    )
    issue_id = "legacy_sensors_" + entry.entry_id
    ir.async_create_issue(
        ha,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="legacy_sensors",
    )
    assert await ha.config_entries.async_reload(entry.entry_id)
    await ha.async_block_till_done()
    issue = ir.async_get(ha).async_get_issue(DOMAIN, issue_id)
    assert issue.is_fixable
    flow = LegacySensorsRepairFlow(entry.entry_id)
    flow.hass = ha
    confirmation = await flow.async_step_init()
    assert confirmation["description_placeholders"] == {"entities": orphan.entity_id}
    assert registry.async_get(orphan.entity_id) is not None
    await flow.async_step_confirm({})
    assert registry.async_get(orphan.entity_id) is None
    assert await ha.config_entries.async_reload(entry.entry_id)
    await ha.async_block_till_done()
    assert ir.async_get(ha).async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.asyncio
async def test_remove_entry_clears_only_its_legacy_repair(running_entry, ha):
    from homeassistant.helpers import issue_registry as ir

    entry, _ = running_entry
    issue_id = "legacy_sensors_" + entry.entry_id
    for key in (issue_id, "legacy_sensors_other_entry"):
        ir.async_create_issue(
            ha,
            DOMAIN,
            key,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="legacy_sensors",
        )
    assert await ha.config_entries.async_remove(entry.entry_id)
    await ha.async_block_till_done()
    assert ir.async_get(ha).async_get_issue(DOMAIN, issue_id) is None
    assert (
        ir.async_get(ha).async_get_issue(DOMAIN, "legacy_sensors_other_entry")
        is not None
    )
    assert entry.entry_id not in ha.data[DOMAIN]
