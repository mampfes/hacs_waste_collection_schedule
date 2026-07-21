import calendar  # noqa: F401 — must import stdlib calendar FIRST
import os
import sys

# Ensure the inner library package is importable.
# IMPORTANT: stdlib calendar must be imported ABOVE before this path is added,
# because HA's calendar.py in this path shadows the stdlib calendar module.
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, cast  # isort:skip

import voluptuous as vol  # isort:skip
from homeassistant.const import CONF_NAME  # isort:skip
from homeassistant.helpers.selector import (  # isort:skip
    BooleanSelector,
    SelectSelector,
)

from waste_collection_schedule.config_params import (  # isort:skip
    alternatives,
    boolean,
    dropdown,
    integer,
    uprn,
)
from custom_components.waste_collection_schedule.config_flow import (  # isort:skip
    WasteCollectionOptionsFlow,
    _build_schema_from_params,
)
from custom_components.waste_collection_schedule.const import (  # isort:skip
    CONF_COLLECTION_TYPES,
    CONF_CUSTOMIZE,
    CONF_SENSORS,
)


def _marker_and_validator(schema: vol.Schema, field_name: str):
    for marker, validator in schema.schema.items():
        if getattr(marker, "schema", marker) == field_name:
            return marker, validator
    raise KeyError(field_name)


def test_integer_selector_coerces_submitted_value() -> None:
    schema = _build_schema_from_params(
        [integer("count")],
        pre_filled={},
        args_input=None,
        include_title=False,
    )

    result = schema({"count": 5.0})

    assert result["count"] == 5
    assert isinstance(result["count"], int)


def test_alternatives_group_members_render_their_widgets() -> None:
    # #6940: fields inside an alternatives() group fell through to a free-text
    # box, losing their dropdown/boolean/... selector. Each member must render
    # with its proper selector instead.
    schema = _build_schema_from_params(
        [
            alternatives(
                [uprn()],
                [dropdown("region", ["A", "B"]), boolean("flag")],
            )
        ],
        pre_filled={},
        args_input=None,
        include_title=False,
    )

    region_marker, region_validator = _marker_and_validator(schema, "region")
    flag_marker, flag_validator = _marker_and_validator(schema, "flag")

    assert isinstance(region_validator, SelectSelector)
    assert isinstance(flag_validator, BooleanSelector)

    # Every member of an alternatives group is optional in the form (validate()
    # enforces that exactly one group is fully provided).
    assert isinstance(region_marker, vol.Optional)
    assert isinstance(flag_marker, vol.Optional)


def test_options_flow_gathers_sensor_collection_types() -> None:
    # #6944: sensors store waste types under CONF_COLLECTION_TYPES, but the
    # options flow read CONF_TYPE, so configured sensor types were never
    # gathered for the edit-sensor list (only customisation keys were).
    class _Entry:
        def __init__(self) -> None:
            self.options = {
                CONF_CUSTOMIZE: {"Glass": {}},
                CONF_SENSORS: [
                    {
                        CONF_NAME: "s1",
                        CONF_COLLECTION_TYPES: ["General Waste", "Recycling"],
                    }
                ],
            }

    flow = object.__new__(WasteCollectionOptionsFlow)
    flow._entry = cast(Any, _Entry())

    types = set(flow.get_types_of_sensors_and_customizations())

    assert {"General Waste", "Recycling"} <= types  # sensor types now included
    assert "Glass" in types  # customisation keys still included
