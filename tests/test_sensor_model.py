"""Persisted sensor compatibility, renderer parity and provider-bin filtering."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
import voluptuous as vol
from freezegun import freeze_time

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)

from waste_collection_schedule import Collection
from waste_collection_schedule.collection import CollectionGroup
from waste_collection_schedule.collection_aggregator import CollectionAggregator
from waste_collection_schedule.source_shell import Customize, SourceShell
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    PAPER,
    RECYCLABLES,
    set_display_language,
)

from custom_components.waste_collection_schedule.config_flow import (
    EXAMPLE_DATE_TEMPLATES,
    EXAMPLE_VALUE_TEMPLATES,
)
from custom_components.waste_collection_schedule.default_sensors import (
    LEGACY_VALUE_TEMPLATE,
    catalogue,
)
from custom_components.waste_collection_schedule.sensor_format import (
    render_date,
    render_state,
)
from custom_components.waste_collection_schedule.sensor_migration import migrate_records
from custom_components.waste_collection_schedule.sensor_model import (
    SensorConfig,
    migrate_filter,
)


def test_catalogue_identity_survives_translation_and_custom_names():
    english = catalogue({"paper": "Paper", "preserved:Local bin": "Local bin"})
    german = catalogue({"paper": "Papier", "preserved:Local bin": "Eigene Tonne"})
    assert english["type:paper"]["id"] == german["type:paper"]["id"] == "type_paper"
    assert (
        english["type:preserved:Local bin"]["id"]
        == german["type:preserved:Local bin"]["id"]
    )
    assert english["next_collection"]["state_format"] == "types"
    with pytest.raises(vol.Invalid):
        SensorConfig(name="Paper", event_index=-1).as_dict()


def test_migration_recognizes_renamed_defaults_and_keeps_ambiguous_bin_filters():
    options = {
        "sensor_select": ["Blaue Tonne"],
        "customize_select": [],
        "customize": {
            "paper": {"alias": "Blaue Tonne"},
            "Recycling large": {"alias": "Large bin"},
        },
        "sensors": [
            {
                "name": "Renamed default",
                "types": ["Blaue Tonne"],
                "value_template": LEGACY_VALUE_TEMPLATE,
                "details_format": "upcoming",
            },
            {
                "name": "Another default",
                "types": ["Blaue Tonne"],
                "value_template": LEGACY_VALUE_TEMPLATE,
                "details_format": "upcoming",
            },
            {
                "name": "Only my bin",
                "types": ["Large bin"],
                "value_template": "{{ value.types[0] | upper }}",
            },
        ],
    }
    result = migrate_records(options, {"paper"})
    first, duplicate, custom = result["sensors"]
    assert (first["id"], first["origin"], first["types"], first["state_format"]) == (
        "type_paper",
        "type:paper",
        ["paper"],
        "date",
    )
    assert duplicate["origin"] == "custom" and duplicate["id"] != first["id"]
    assert custom["types"] == ["Large bin"]
    assert custom["value_template"] == "{{ value.types[0] | upper }}"
    assert "sensor_select" not in result and "customize_select" not in result
    assert result["auto_add_types"] is False
    assert migrate_records(result)["sensors"] == result["sensors"]
    assert options["sensors"][0]["types"] == ["Blaue Tonne"]


def test_migration_keeps_separator_sensitive_and_unknown_templates():
    value = EXAMPLE_VALUE_TEMPLATES[".. in .. days"]
    result = migrate_records(
        {"separator": " / ", "sensors": [{"name": "Next", "value_template": value}]}
    )["sensors"][0]
    assert result["state_format"] == "custom" and result["value_template"] == value
    assert (
        migrate_filter("Restmüll 4-wöchentlich", {}, {"paper"})
        == "Restmüll 4-wöchentlich"
    )
    assert migrate_filter("Papier", {}, {"paper"}) == "paper"
    assert migrate_filter("Paper", {}, set()) == "Paper"


@pytest.mark.parametrize(
    "name,template", [(k, v) for k, v in EXAMPLE_VALUE_TEMPLATES.items() if v]
)
@pytest.mark.parametrize("days", [0, 1, 3, 7])
def test_migrated_state_presets_render_exact_legacy_text(name, template, days):
    from jinja2 import Template

    with freeze_time("2026-10-31"):
        collection = CollectionGroup.create(
            [
                Collection(
                    date=date(2026, 10, 31) + timedelta(days=days), waste_type=PAPER
                )
            ]
        )
        record = migrate_records(
            {"sensors": [{"name": "Next", "value_template": template}]}
        )["sensors"][0]
        assert render_state(
            collection,
            record["state_format"],
            record["date_format"],
            record["language"],
            ", ",
        ) == Template(template).render(value=collection)


@pytest.mark.parametrize("template", [v for v in EXAMPLE_DATE_TEMPLATES.values() if v])
def test_migrated_date_presets_render_exact_legacy_text(template):
    from jinja2 import Template

    collection = Collection(date=date(2026, 10, 31), waste_type=PAPER)
    record = migrate_records(
        {"sensors": [{"name": "Next", "date_template": template}]}
    )["sensors"][0]
    assert render_date(collection.date, record["date_format"], "en") == Template(
        template
    ).render(value=collection)


@pytest.mark.parametrize(
    "language,today,tomorrow",
    [
        ("en", "Today", "Tomorrow"),
        ("de", "Heute", "Morgen"),
        ("fr", "Aujourd'hui", "Demain"),
        ("it", "Oggi", "Domani"),
        ("nl", "Vandaag", "Morgen"),
        ("sl", "Danes", "Jutri"),
        ("da", "I dag", "I morgen"),
        ("fi", "Tänään", "Huomenna"),
        ("sv", "I dag", "I morgon"),
        ("nb", "I dag", "I morgen"),
    ],
)
def test_relative_rendering_is_localized(language, today, tomorrow):
    with freeze_time("2026-10-31"):
        for days, expected in ((0, today), (1, tomorrow)):
            collection = CollectionGroup.create(
                [
                    Collection(
                        date=date(2026, 10, 31) + timedelta(days=days), waste_type=PAPER
                    )
                ]
            )
            assert (
                render_state(collection, "relative", "iso", language, ", ") == expected
            )


class BinsSource:
    def fetch(self):
        transform = JsonTransformer(
            date_key="date",
            type_key="bin",
            type_value_map={"Small": RECYCLABLES, "Large": RECYCLABLES, "Paper": PAPER},
            color_key="color",
            carry_raw_label=True,
        )
        return [
            transform(r)
            for r in [
                {"date": "2099-01-01", "bin": "Small", "color": "#111111"},
                {"date": "2099-01-01", "bin": "Large", "color": "#222222"},
                {"date": "2099-01-02", "bin": "Small", "color": "#111111"},
                {"date": "2099-01-03", "bin": "Paper", "color": "#333333"},
            ]
        ]


def test_label_filter_before_merge_and_hidden_labels_preserve_bin_metadata():
    shell = SourceShell(
        source=BinsSource(),
        title="Fixture",
        description="Synthetic bins",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
        customize={
            "recyclables": Customize("recyclables", color="#AAAAAA"),
            "Large": Customize("Large", color="#BBBBBB"),
        },
        ignore_duplicates=True,
        show_original_label=False,
    )
    shell.fetch()
    aggregator = CollectionAggregator([shell])
    selected = aggregator.get_upcoming(include_types=["Large"])
    assert [(c.date, c.original_label, c.color) for c in selected] == [
        (date(2099, 1, 1), "Large", "#BBBBBB")
    ]
    overview = aggregator.get_upcoming_group_by_day(count=1)[0].as_dict()
    assert [(r["original_label"], r["color"]) for r in overview["collections"]] == [
        ("Small", "#AAAAAA"),
        ("Large", "#BBBBBB"),
    ]
    assert [
        r.original_label for r in aggregator.get_upcoming(preserve_bins=True, count=2)
    ] == ["Small", "Large"]
    assert selected[0].description is None
    assert selected[0].as_dict()["original_label"] == "Large"
    assert selected[0].as_dict()["type_id"] == "recyclables"
    assert [
        c.original_label for c in aggregator.get_upcoming(exclude_types=["Small"])
    ] == ["Large", "Paper"]


def test_unique_types_keeps_earliest_bin_before_index_and_group_limits():
    shell = SourceShell(
        source=BinsSource(),
        customize={},
        title="Fixture",
        description="Synthetic bins",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
        ignore_duplicates=True,
    )
    shell.fetch()
    aggregator = CollectionAggregator([shell])
    unique = aggregator.get_upcoming(unique_types=True)
    assert [c.original_label for c in unique] == ["Small", "Large", "Paper"]
    grouped = aggregator.get_upcoming_group_by_day(unique_types=True, count=1)
    assert grouped[0].types == [RECYCLABLES.names["en"], RECYCLABLES.names["en"]]
    assert aggregator.get_upcoming_group_by_day(
        unique_types=True, start_index=1, count=1
    )[0].date == date(2099, 1, 3)
    set_display_language("de")
    try:
        assert [
            c.original_label
            for c in aggregator.get_upcoming(
                include_types=["recyclables"], unique_types=True
            )
        ] == ["Small", "Large"]
    finally:
        set_display_language("en")


def test_filtered_duplicates_merge_descriptions_without_mutating_bin_records():
    shell = SourceShell(
        source=BinsSource(),
        customize={},
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
    grouped = aggregator.get_upcoming_group_by_day(include_types=["recyclables"])[0]
    assert grouped.description == "Small, Large"
    assert [r["description"] for r in grouped.as_dict()["collections"]] == [
        "Small",
        "Large",
    ]
    assert aggregator.get_upcoming(include_types=["Small"])[0].description == "Small"
    assert [e.description for e in shell._sensor_entries[:2]] == ["Small", "Large"]


@pytest.mark.parametrize("show_original_label", [False, True])
def test_raw_label_identity_keeps_internal_whitespace(show_original_label):
    class Source:
        def fetch(self):
            return [
                JsonTransformer(
                    date_key="date",
                    type_key="bin",
                    carry_raw_label=True,
                    type_value_map={"Small  bin": RECYCLABLES},
                )({"date": "2099-01-01", "bin": "Small  bin"})
            ]

    shell = SourceShell(
        source=Source(),
        customize={"Small  bin": Customize("Small  bin", color="#123456")},
        title="Fixture",
        description="Bins",
        url=None,
        calendar_title=None,
        unique_id="fixture",
        day_offset=0,
        show_original_label=show_original_label,
    )
    shell.fetch()
    selected = CollectionAggregator([shell]).get_upcoming(include_types=["Small  bin"])
    assert len(selected) == 1
    assert selected[0].original_label == "Small  bin"
    assert selected[0].color == "#123456"
    assert selected[0].description == ("Small bin" if show_original_label else None)
