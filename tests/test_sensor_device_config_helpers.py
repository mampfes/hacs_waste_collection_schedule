import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.sensor_config_helpers import (  # noqa: E402
    COMBINED_SENSOR_NAME,
    build_added_combined_sensor_options,
    build_added_collection_type_sensor_options,
    build_combined_waste_sensor,
    build_legacy_ui_sensor_unique_id,
    build_remove_ui_sensor_action_unique_id,
    build_removed_sensor_options,
    build_stable_ui_sensor_unique_id,
    build_sensor_for_collection_type,
    build_ui_sensor_control_unique_id,
    build_ui_sensor_device_identifier,
    build_ui_sensor_unique_id,
    configured_sensor_ids,
    configured_collection_types,
    ensure_sensor_ids,
    has_combined_sensor,
    iter_ui_sensor_unique_id_migrations,
    missing_collection_types,
    parse_stable_ui_sensor_id,
    parse_ui_sensor_device_id,
    parse_ui_sensor_device_identifier,
    remove_sensor_config_by_id,
    replace_sensor_config,
    update_sensor_config_list,
    update_sensor_config_list_by_id,
)
from custom_components.waste_collection_schedule.sensor_template_presets import (  # noqa: E402
    PL_RELATIVE_TEMPLATE,
    CUSTOM_OPTION,
    DEFAULT_OPTION,
    PRESET_LANGUAGE_OPTIONS,
    VALUE_TEMPLATE_PRESETS,
    convert_value_template_language,
    format_default_state_text,
    get_preset_option,
    get_value_template_presets,
)

CONF_NAME = "name"
CONF_SENSOR_ID = "sensor_id"
CONF_DETAILS_FORMAT = "details_format"
CONF_VALUE_TEMPLATE = "value_template"


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


def test_display_language_options_cover_translation_files():
    translations_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waste_collection_schedule",
        "translations",
    )
    translation_languages = {
        os.path.splitext(filename)[0]
        for filename in os.listdir(translations_dir)
        if filename.endswith(".json")
    }

    assert set(PRESET_LANGUAGE_OPTIONS.values()) == translation_languages


def test_display_language_translation_keys_exist_for_all_translations():
    translations_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waste_collection_schedule",
        "translations",
    )

    for filename in os.listdir(translations_dir):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(translations_dir, filename), encoding="utf-8") as file:
            translation = json.load(file)
        sensor_step = translation["config"]["step"]["sensor"]
        if "sections" in sensor_step:
            sensor_data = sensor_step["sections"]["display"]["data"]
        else:
            sensor_data = sensor_step.get("data", {})
        assert "preset_language" in sensor_data


def test_default_state_text_supports_all_display_languages():
    assert format_default_state_text(["Bio"], 2, ", ", "de") == "Bio in 2 Tagen"
    assert format_default_state_text(["Bio"], 2, ", ", "fr") == "Bio dans 2 jours"
    assert format_default_state_text(["Bio"], 2, ", ", "it") == "Bio tra 2 giorni"
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


def test_get_preset_option_returns_custom_for_unknown_template():
    assert get_preset_option("{{value.date}}", VALUE_TEMPLATE_PRESETS) == CUSTOM_OPTION


def test_update_sensor_config_list_updates_only_matching_sensor():
    sensors = [
        {CONF_NAME: "Bio", CONF_VALUE_TEMPLATE: "old"},
        {CONF_NAME: "Paper"},
    ]

    updated = update_sensor_config_list(
        sensors,
        sensor_name="Bio",
        updates={CONF_VALUE_TEMPLATE: "new"},
    )

    assert updated[0][CONF_VALUE_TEMPLATE] == "new"
    assert CONF_VALUE_TEMPLATE not in updated[1]
    assert sensors[0][CONF_VALUE_TEMPLATE] == "old"


def test_update_sensor_config_list_can_remove_keys():
    sensors = [{CONF_NAME: "Bio", CONF_VALUE_TEMPLATE: "old"}]

    updated = update_sensor_config_list(
        sensors,
        sensor_name="Bio",
        removals=(CONF_VALUE_TEMPLATE,),
    )

    assert CONF_VALUE_TEMPLATE not in updated[0]


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


def test_replace_sensor_config_replaces_only_target_sensor():
    sensors = [
        {CONF_NAME: "Bio", CONF_VALUE_TEMPLATE: "old"},
        {CONF_NAME: "Paper"},
    ]

    updated = replace_sensor_config(
        sensors,
        original_sensor_name="Bio",
        replacement={CONF_NAME: "Bio Friendly", CONF_VALUE_TEMPLATE: "new"},
    )

    assert updated[0][CONF_NAME] == "Bio Friendly"
    assert updated[0][CONF_VALUE_TEMPLATE] == "new"
    assert updated[1][CONF_NAME] == "Paper"
    assert sensors[0][CONF_NAME] == "Bio"


def test_ensure_sensor_ids_only_fills_missing_ids():
    sensors = [
        {CONF_NAME: "Bio"},
        {CONF_NAME: "Paper", CONF_SENSOR_ID: "keep-me"},
    ]

    values = iter(["generated-id"])
    updated, changed = ensure_sensor_ids(sensors, id_factory=lambda: next(values))

    assert changed is True
    assert updated[0][CONF_SENSOR_ID] == "generated-id"
    assert updated[1][CONF_SENSOR_ID] == "keep-me"
    assert CONF_SENSOR_ID not in sensors[0]


def test_missing_collection_types_ignores_types_already_covered_by_sensors():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]},
        {CONF_NAME: "All", CONF_SENSOR_ID: "all-id"},
    ]

    assert missing_collection_types({"Bio", "Paper", "Glass"}, sensors) == [
        "Glass",
        "Paper",
    ]


def test_missing_collection_types_treats_alias_and_raw_type_as_covered():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id", "types": ["Bio"]},
    ]
    customizations = {"BIO (wrzucamy bez worków - luzem)": {"alias": "Bio"}}

    assert missing_collection_types(
        {"BIO (wrzucamy bez worków - luzem)", "Paper"},
        sensors,
        customizations,
    ) == ["Paper"]


def test_build_sensor_for_collection_type_creates_default_per_type_sensor():
    sensor = build_sensor_for_collection_type("Bio", id_factory=lambda: "bio-id")

    assert sensor == {
        CONF_NAME: "Bio",
        CONF_SENSOR_ID: "bio-id",
        CONF_DETAILS_FORMAT: "upcoming",
        "types": ["Bio"],
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
        options = {
            "sensors": [
                {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
                {CONF_NAME: "Paper", CONF_SENSOR_ID: "paper-id"},
            ]
        }

    options = build_removed_sensor_options(Entry(), "paper-id")

    assert options["sensors"] == [{CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"}]


def test_build_added_collection_type_sensor_options_appends_new_sensor():
    class Entry:
        options = {"sensors": [{CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"}]}

    options = build_added_collection_type_sensor_options(
        Entry(), "Paper", id_factory=lambda: "paper-id"
    )

    assert options["sensors"] == [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {
            CONF_NAME: "Paper",
            CONF_SENSOR_ID: "paper-id",
            CONF_DETAILS_FORMAT: "upcoming",
            "types": ["Paper"],
        },
    ]


def test_build_added_combined_sensor_options_appends_new_sensor():
    class Entry:
        options = {"sensors": [{CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"}]}

    options = build_added_combined_sensor_options(
        Entry(), id_factory=lambda: "combined-id"
    )

    assert options["sensors"] == [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {
            CONF_NAME: COMBINED_SENSOR_NAME,
            CONF_SENSOR_ID: "combined-id",
            CONF_DETAILS_FORMAT: "upcoming",
        },
    ]


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
    assert parse_ui_sensor_device_identifier("source-1", "other_sensor_sensor-1") is None
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


def test_build_remove_ui_sensor_action_unique_id_uses_stable_sensor_id():
    assert build_remove_ui_sensor_action_unique_id("source-1", "sensor-1") == (
        "source-1_ui_sensor_action_remove_sensor-1"
    )


def test_parse_stable_ui_sensor_id_supports_sensor_and_control_entities():
    assert parse_stable_ui_sensor_id(
        "source-1", "source-1_ui_sensor_sensor-1"
    ) == "sensor-1"
    assert parse_stable_ui_sensor_id(
        "source-1", "source-1_ui_sensor_control_sensor-1_mode"
    ) == "sensor-1"
    assert parse_stable_ui_sensor_id(
        "source-1", "source-1_ui_sensor_action_remove_sensor-1"
    ) == "sensor-1"


def test_parse_stable_ui_sensor_id_ignores_other_unique_ids():
    assert parse_stable_ui_sensor_id(
        "source-1", "source-1_ui_sensor_action_create_Bio"
    ) is None
    assert parse_stable_ui_sensor_id("source-1", "other_ui_sensor_sensor-1") is None


def test_iter_ui_sensor_unique_id_migrations_returns_name_to_id_pairs():
    sensors = [
        {CONF_NAME: "Bio", CONF_SENSOR_ID: "bio-id"},
        {CONF_NAME: "Paper"},
        {CONF_SENSOR_ID: "missing-name"},
    ]

    assert iter_ui_sensor_unique_id_migrations("source-1", sensors) == [
        (
            build_legacy_ui_sensor_unique_id("source-1", "Bio"),
            build_stable_ui_sensor_unique_id("source-1", "bio-id"),
        )
    ]
