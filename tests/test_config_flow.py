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

import voluptuous as vol  # isort:skip
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
    _build_schema_from_params,
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
