import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule import button as button_module
from custom_components.waste_collection_schedule.sensor_config_helpers import (
    COMBINED_SENSOR_NAME,
    build_added_collection_type_sensor_options,
    build_added_combined_sensor_options,
    build_combined_waste_sensor,
    build_create_combined_ui_sensor_action_unique_id,
    build_create_ui_sensor_action_unique_id,
    build_legacy_ui_sensor_unique_id,
    build_removed_sensor_options,
    build_sensor_for_collection_type,
    build_ui_sensor_control_unique_id,
    build_ui_sensor_device_identifier,
    build_ui_sensor_unique_id,
    configured_collection_types,
    configured_sensor_ids,
    ensure_sensor_ids,
    has_combined_sensor,
    missing_collection_types,
    parse_ui_sensor_device_id,
    parse_ui_sensor_device_identifier,
    preserve_device_control_options,
    preserve_sensor_control_metadata,
    remove_sensor_config_by_id,
    update_sensor_config_list_by_id,
)
from custom_components.waste_collection_schedule.sensor_template_presets import (
    CUSTOM_OPTION,
    DEFAULT_OPTION,
    NL_RELATIVE_TEMPLATE,
    PL_RELATIVE_TEMPLATE,
    PRESET_LANGUAGE_OPTIONS,
    VALUE_TEMPLATE_PRESETS,
    convert_value_template_language,
    format_default_state_text,
    get_preset_option,
    get_value_template_presets,
)

CONF_NAME = "name"
CONF_SENSOR_ID = "sensor_id"
CONF_SENSOR_LEGACY_UNIQUE_ID = "sensor_legacy_unique_id"
CONF_DETAILS_FORMAT = "details_format"
CONF_VALUE_TEMPLATE = "value_template"
CONF_PRESET_LANGUAGE = "preset_language"
CONF_DEVICE_SENSOR_CONTROLS = "device_sensor_controls"


def test_get_preset_option_returns_default_for_empty_template():
    assert get_preset_option("", VALUE_TEMPLATE_PRESETS) == DEFAULT_OPTION


def test_get_preset_option_returns_matching_label_for_known_template():
    assert (
        get_preset_option("in {{value.daysTo}} days", VALUE_TEMPLATE_PRESETS)
        == "in 13 days"
    )


def test_get_preset_option_returns_matching_label_for_polish_template():
    assert (
        get_preset_option("za {{value.daysTo}} dni", get_value_template_presets("pl"))
        == "za 13 dni"
    )


def test_grouped_value_template_presets_use_group_friendly_labels():
    presets = get_value_template_presets("en", grouped=True)

    assert "Waste types in 13 days" in presets
    assert "Bio in 13 days" not in presets
    assert presets["Waste types in 13 days"] == (
        '{{value.types|join(", ")}} in {{value.daysTo}} days'
    )


def test_display_language_options_cover_supported_sensor_presets():
    assert set(PRESET_LANGUAGE_OPTIONS.values()) == {"de", "en", "fr", "it", "nl", "pl"}


def test_display_language_presets_exist_for_all_supported_languages():
    for language in PRESET_LANGUAGE_OPTIONS.values():
        assert get_value_template_presets(language)


def test_default_state_text_supports_all_display_languages():
    assert format_default_state_text(["Bio"], 2, ", ", "de") == "Bio in 2 Tagen"
    assert format_default_state_text(["Bio"], 2, ", ", "fr") == "Bio dans 2 jours"
    assert format_default_state_text(["Bio"], 2, ", ", "it") == "Bio tra 2 giorni"
    assert format_default_state_text(["Bio"], 2, ", ", "nl") == "Bio over 2 dagen"
    assert format_default_state_text(["Bio"], 2, ", ", "pl") == "Bio za 2 dni"


def test_convert_value_template_language_maps_known_preset():
    assert (
        convert_value_template_language(
            "{% if value.daysTo == 0 %}Today{% elif value.daysTo == 1 %}Tomorrow"
            "{% else %}in {{value.daysTo}} days{% endif %}",
            "pl",
        )
        == PL_RELATIVE_TEMPLATE
    )
    assert (
        convert_value_template_language(PL_RELATIVE_TEMPLATE, "nl")
        == NL_RELATIVE_TEMPLATE
    )


def test_get_preset_option_returns_custom_for_unknown_template():
    assert get_preset_option("{{value.date}}", VALUE_TEMPLATE_PRESETS) == CUSTOM_OPTION


def test_update_sensor_config_list_by_id_updates_only_matching_sensor():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {CONF_NAME: "Paper", CONF_SENSOR_ID: "paper-id"},
    ]

    updated = update_sensor_config_list_by_id(
        sensors,
        sensor_id="paper-id",
        updates={CONF_VALUE_TEMPLATE: "new"},
    )

    assert CONF_VALUE_TEMPLATE not in updated[0]
    assert updated[1][CONF_VALUE_TEMPLATE] == "new"
    assert CONF_VALUE_TEMPLATE not in sensors[1]


def test_remove_sensor_config_by_id_removes_only_matching_sensor():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {CONF_NAME: "Paper", CONF_SENSOR_ID: "paper-id"},
    ]

    updated = remove_sensor_config_by_id(sensors, "bio-id")

    assert updated == [{CONF_NAME: "Paper", CONF_SENSOR_ID: "paper-id"}]
    assert len(sensors) == 2


def test_ensure_sensor_ids_only_fills_missing_ids():
    sensors = [
        {CONF_NAME: "Bio"},
        {CONF_NAME: "Paper", CONF_SENSOR_ID: "keep-me"},
    ]

    values = iter(["generated-id"])
    updated, changed = ensure_sensor_ids(sensors, id_factory=lambda: next(values))

    assert changed is True
    assert updated[0][CONF_SENSOR_ID] == "generated-id"
    assert updated[0][CONF_SENSOR_LEGACY_UNIQUE_ID] is True
    assert updated[1][CONF_SENSOR_ID] == "keep-me"
    assert CONF_SENSOR_LEGACY_UNIQUE_ID not in updated[1]
    assert CONF_SENSOR_ID not in sensors[0]


def test_missing_collection_types_ignores_types_already_covered_by_sensors():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]},
        {CONF_NAME: "All", CONF_SENSOR_ID: "all-id"},
    ]

    assert missing_collection_types(
        {"organic": "Bio", "paper": "Paper", "glass": "Glass"}, sensors
    ) == [
        ("glass", "Glass"),
        ("paper", "Paper"),
    ]


def test_missing_collection_types_treats_display_label_as_stable_id_coverage():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]},
    ]
    assert missing_collection_types(
        {
            "organic": "Bio",
            "paper": "Paper",
        },
        sensors,
    ) == [("paper", "Paper")]


def test_missing_collection_types_resolves_legacy_alias_across_languages():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": [" BIO "]},
    ]

    assert missing_collection_types(
        {"organic": "Biomüll", "paper": "Altpapier"},
        sensors,
    ) == [("paper", "Altpapier")]


def test_build_sensor_for_collection_type_creates_default_per_type_sensor():
    sensor = build_sensor_for_collection_type(
        "organic", "Bio", id_factory=lambda: "bio-id"
    )

    assert sensor == {
        CONF_NAME: "Bio",
        CONF_SENSOR_ID: "bio-id",
        CONF_DETAILS_FORMAT: "upcoming",
        "types": ["organic"],
    }


def test_has_combined_sensor_detects_sensor_without_type_filter():
    assert has_combined_sensor([{CONF_NAME: "Everything"}]) is True
    assert has_combined_sensor([{CONF_NAME: "Bio", "types": ["Bio"]}]) is False


def test_build_combined_waste_sensor_creates_all_type_sensor():
    sensor = build_combined_waste_sensor(id_factory=lambda: "combined-id")

    assert sensor == {
        CONF_NAME: COMBINED_SENSOR_NAME,
        CONF_SENSOR_ID: "combined-id",
        CONF_DETAILS_FORMAT: "upcoming",
    }
    assert "types" not in sensor


def test_build_removed_sensor_options_removes_sensor_from_entry_options():
    class Entry:
        def __init__(self):
            self.options = {
                "sensors": [
                    {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
                    {CONF_NAME: "Paper", CONF_SENSOR_ID: "paper-id"},
                ]
            }

    options = build_removed_sensor_options(Entry(), "paper-id")

    assert options["sensors"] == [{CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"}]


def test_build_added_collection_type_sensor_options_appends_new_sensor():
    class Entry:
        def __init__(self):
            self.options = {
                "sensors": [
                    {
                        CONF_NAME: "Bio",
                        CONF_SENSOR_ID: "bio-id",
                        "types": ["organic"],
                    }
                ]
            }

    options = build_added_collection_type_sensor_options(
        Entry(), "paper", "Paper", id_factory=lambda: "paper-id"
    )

    assert options["sensors"] == [
        {
            CONF_NAME: "Bio",
            CONF_SENSOR_ID: "bio-id",
            "types": ["organic"],
        },
        {
            CONF_NAME: "Paper",
            CONF_SENSOR_ID: "paper-id",
            CONF_DETAILS_FORMAT: "upcoming",
            "types": ["paper"],
        },
    ]


def test_build_added_collection_type_sensor_options_is_idempotent():
    class Entry:
        def __init__(self):
            self.options = {
                "sensors": [
                    {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]}
                ]
            }

    options = build_added_collection_type_sensor_options(
        Entry(),
        "organic",
        "Biomüll",
        id_factory=lambda: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert options["sensors"] == [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]}
    ]


def test_build_added_combined_sensor_options_appends_new_sensor():
    class Entry:
        def __init__(self):
            self.options = {
                "sensors": [
                    {
                        CONF_NAME: "Bio",
                        CONF_SENSOR_ID: "bio-id",
                        "types": ["organic"],
                    }
                ]
            }

    options = build_added_combined_sensor_options(
        Entry(), id_factory=lambda: "combined-id"
    )

    assert options["sensors"] == [
        {
            CONF_NAME: "Bio",
            CONF_SENSOR_ID: "bio-id",
            "types": ["organic"],
        },
        {
            CONF_NAME: COMBINED_SENSOR_NAME,
            CONF_SENSOR_ID: "combined-id",
            CONF_DETAILS_FORMAT: "upcoming",
        },
    ]


def test_build_added_combined_sensor_options_is_idempotent():
    class Entry:
        def __init__(self):
            self.options = {
                "sensors": [{CONF_NAME: "Everything", CONF_SENSOR_ID: "all-id"}]
            }

    options = build_added_combined_sensor_options(
        Entry(),
        id_factory=lambda: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert options["sensors"] == [{CONF_NAME: "Everything", CONF_SENSOR_ID: "all-id"}]


def test_configured_collection_types_returns_selected_sensor_types():
    sensors = [
        {CONF_NAME: "Bio", "types": ["Bio"]},
        {CONF_NAME: "Mixed", "types": ["Paper", "Glass"]},
        {CONF_NAME: "Everything"},
    ]

    assert configured_collection_types(sensors) == {"Bio", "Glass", "Paper"}


def test_configured_sensor_ids_returns_stable_sensor_ids():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {CONF_NAME: "Legacy"},
    ]

    assert configured_sensor_ids(sensors) == {"bio-id"}


def test_build_ui_sensor_unique_id_uses_stable_id_when_available():
    assert (
        build_ui_sensor_unique_id("source-1", "Bio", "sensor-1")
        == "source-1_ui_sensor_sensor-1"
    )


def test_build_ui_sensor_unique_id_falls_back_to_legacy_name():
    assert build_ui_sensor_unique_id("source-1", "Bio", None) == (
        "source-1_ui_sensor_Bio"
    )


def test_build_ui_sensor_unique_id_preserves_existing_entity_identity():
    assert build_ui_sensor_unique_id(
        "source-1",
        "Bio",
        "sensor-1",
        preserve_legacy_unique_id=True,
    ) == build_legacy_ui_sensor_unique_id("source-1", "Bio")


def test_build_ui_sensor_device_identifier_uses_stable_sensor_id():
    assert (
        build_ui_sensor_device_identifier("source-1", "sensor-1")
        == "source-1_sensor_sensor-1"
    )


def test_parse_ui_sensor_device_identifier_returns_stable_sensor_id():
    assert (
        parse_ui_sensor_device_identifier("source-1", "source-1_sensor_sensor-1")
        == "sensor-1"
    )


def test_parse_ui_sensor_device_identifier_ignores_other_identifiers():
    assert (
        parse_ui_sensor_device_identifier("source-1", "other_sensor_sensor-1") is None
    )
    assert parse_ui_sensor_device_identifier("source-1", "source-1") is None


def test_parse_ui_sensor_device_id_uses_domain_identifier():
    assert (
        parse_ui_sensor_device_id(
            "source-1",
            {
                ("other_domain", "source-1_sensor_sensor-1"),
                ("waste_collection_schedule", "source-1_sensor_sensor-2"),
            },
        )
        == "sensor-2"
    )


def test_build_ui_sensor_control_unique_id_uses_stable_sensor_id():
    assert build_ui_sensor_control_unique_id("source-1", "sensor-1", "mode") == (
        "source-1_ui_sensor_control_sensor-1_mode"
    )


def test_build_create_ui_sensor_action_unique_ids_are_stable():
    assert (
        build_create_combined_ui_sensor_action_unique_id("source-1")
        == "source-1_ui_sensor_action_create_combined"
    )
    assert (
        build_create_ui_sensor_action_unique_id("source-1", "Bio")
        == "source-1_ui_sensor_action_create_Bio"
    )


def test_legacy_editor_round_trip_preserves_device_control_metadata():
    existing_options = {
        CONF_DEVICE_SENSOR_CONTROLS: True,
        "sensors": [
            {
                CONF_NAME: "Bio",
                CONF_SENSOR_ID: "bio-id",
                CONF_SENSOR_LEGACY_UNIQUE_ID: True,
                CONF_PRESET_LANGUAGE: "pl",
                "types": ["organic"],
            }
        ],
    }
    submitted_options = {"separator": " / "}
    submitted_sensor = {CONF_NAME: "Bio renamed", "types": ["organic"]}

    updated_options = preserve_device_control_options(
        existing_options,
        submitted_options,
    )
    updated_sensor = preserve_sensor_control_metadata(
        existing_options["sensors"][0],
        submitted_sensor,
    )
    updated_options["sensors"] = [updated_sensor]

    assert updated_options == {
        CONF_DEVICE_SENSOR_CONTROLS: True,
        "separator": " / ",
        "sensors": [
            {
                CONF_NAME: "Bio renamed",
                CONF_SENSOR_ID: "bio-id",
                CONF_SENSOR_LEGACY_UNIQUE_ID: True,
                CONF_PRESET_LANGUAGE: "pl",
                "types": ["organic"],
            }
        ],
    }


def test_button_platform_adds_new_type_actions_after_later_fetch(monkeypatch):
    class Aggregator:
        def __init__(self):
            self.type_options = {}

    class Shell:
        unique_id = "source-1"

    class Coordinator:
        def __init__(self):
            self.shell = Shell()
            self.device_info = "service-device"
            self._aggregator = Aggregator()

    class Entry:
        def __init__(self):
            self.entry_id = "entry-1"
            self.options = {CONF_DEVICE_SENSOR_CONTROLS: True, "sensors": []}
            self.unload_callbacks = []

        def async_on_unload(self, callback):
            self.unload_callbacks.append(callback)

    class Hass:
        def __init__(self, coordinator):
            self.data = {"waste_collection_schedule": {"entry-1": coordinator}}

    coordinator = Coordinator()
    entry = Entry()
    dispatcher_callbacks = []
    added_entities = []

    def connect(_hass, _signal, callback):
        dispatcher_callbacks.append(callback)
        return lambda: None

    monkeypatch.setattr(button_module, "async_dispatcher_connect", connect)

    asyncio.run(
        button_module.async_setup_entry(
            Hass(coordinator),
            entry,
            lambda entities: added_entities.extend(entities),
        )
    )

    assert len(added_entities) == 1
    assert len(dispatcher_callbacks) == 1
    assert len(entry.unload_callbacks) == 1

    coordinator._aggregator.type_options = {"organic": "Organic Waste"}
    dispatcher_callbacks[0]()
    dispatcher_callbacks[0]()

    assert len(added_entities) == 2
    assert isinstance(added_entities[1], button_module.CreateWasteSensorButton)
