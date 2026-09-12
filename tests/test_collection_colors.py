"""Provider colors survive mapping, customization and HA serialization."""

import calendar  # noqa: F401
import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.append(
    str(Path(__file__).parents[1] / "custom_components/waste_collection_schedule")
)

from waste_collection_schedule import Collection
from waste_collection_schedule.collection import CollectionGroup
from waste_collection_schedule.source.ecoharmonogram_pl import Source
from waste_collection_schedule.source_shell import Customize, customize_function
from waste_collection_schedule.waste_types import ORGANIC, PAPER

D = date(2099, 9, 14)


def test_provider_color_is_per_collection_and_does_not_change_global_type():
    local = Collection(date=D, waste_type=ORGANIC, color="#9e5e23")
    other = Collection(date=D, waste_type=ORGANIC, color="#123456")
    default = Collection(date=D, waste_type=ORGANIC)
    assert [c.color for c in [local, other, default]] == [
        "#9E5E23",
        "#123456",
        ORGANIC.color,
    ]
    assert local.as_dict()["type_id"] == "organic"
    assert [c.color_source for c in [local, default]] == ["source", "default"]


@pytest.mark.parametrize("color", [None, "", "brown", "#123", "#zzzzzz", 42])
def test_invalid_provider_color_falls_back(color):
    entry = Collection(date=D, waste_type=ORGANIC, color=color)
    assert entry.color == ORGANIC.color
    assert entry.color_source == "default"


def test_customization_overrides_color_without_changing_type_identity():
    entry = Collection(date=D, waste_type=ORGANIC, color="#9e5e23")
    customize_function(
        entry, {entry.type: Customize(entry.type, alias="Garden bin", color="#abcdef")}
    )
    assert entry.type == "Garden bin"
    assert entry.color == "#ABCDEF"
    assert entry.color_source == "customize"
    assert entry.as_dict()["type_id"] == "organic"
    entry.set_color(None)
    assert entry.color == "#9E5E23"
    assert entry.color_source == "source"
    with pytest.raises(ValueError):
        Customize("Garden bin", color="brown")


def test_legacy_constructor_supports_provider_color():
    entry = Collection(date=D, t="Local bin", color="#123456")
    assert entry.type == "Local bin"
    assert entry.color == "#123456"


def test_same_day_group_serializes_each_collection_color():
    entries = [
        Collection(date=D, waste_type=ORGANIC, color="#9e5e23"),
        Collection(date=D, waste_type=PAPER),
    ]
    grouped = CollectionGroup.create(entries).as_dict()
    assert grouped["types"] == [c.type for c in entries]
    assert [(c["type_id"], c["color"]) for c in grouped["collections"]] == [
        ("organic", "#9E5E23"),
        ("paper", PAPER.color),
    ]
    assert "color" not in grouped


def test_ecoharmonogram_keeps_display_color_for_known_and_unknown_labels():
    raw = {
        "reports": [
            {
                "scheduleDescription": [
                    {"id": "bio", "name": "Bio (2 x miesiąc)", "color": "#9e5e23"},
                    {"id": "payment", "name": "Termin płatności", "color": "#ff0000"},
                ],
                "schedules": [
                    {
                        "scheduleDescriptionId": key,
                        "year": 2099,
                        "month": 9,
                        "days": "14;",
                    }
                    for key in ["bio", "payment"]
                ],
            }
        ]
    }
    records = Source.parse(raw)
    entries = [Source.transform(record) for record in records]
    assert entries[0].waste_type == ORGANIC
    assert entries[0].color == "#9E5E23"
    assert entries[1].type == "Termin płatności"
    assert entries[1].color == "#FF0000"
    assert entries[1].waste_type.id != ORGANIC.id


def test_home_assistant_json_emits_color_metadata():
    from homeassistant.helpers.json import json_bytes

    entry = Collection(date=D, waste_type=ORGANIC, color="#9e5e23")
    payload = json.loads(json_bytes({"upcoming": [entry]}))
    assert payload["upcoming"][0]["color"] == "#9E5E23"
    assert payload["upcoming"][0]["type_id"] == "organic"
    assert payload["upcoming"][0]["color_source"] == "source"


def test_provider_can_supply_a_local_color_mapping():
    from waste_collection_schedule.transformers import JsonTransformer

    colors = {"Local organics": "#795548"}
    transform = JsonTransformer(
        date_key="day",
        type_key="label",
        type_value_map={"Local organics": ORGANIC},
        color_key=lambda row: colors.get(row["label"]),
    )
    entry = transform({"day": D, "label": "Local organics"})
    assert entry.waste_type == ORGANIC
    assert entry.color == "#795548"


def test_yaml_color_validation_normalizes_and_rejects_invalid_overrides():
    import homeassistant  # noqa: F401
    import voluptuous as vol

    from custom_components.waste_collection_schedule.init_yaml import CUSTOMIZE_CONFIG

    assert (
        CUSTOMIZE_CONFIG({"type": "organic", "color": "#abcdef"})["color"] == "#ABCDEF"
    )
    with pytest.raises(vol.Invalid):
        CUSTOMIZE_CONFIG({"type": "organic", "color": "brown"})
