import asyncio
import calendar  # noqa: F401 — must import stdlib calendar FIRST
import importlib
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

# Home Assistant selects its validation implementation during startup. Import it
# before voluptuous so current HA and the minimum supported version share types.
from homeassistant.const import CONF_NAME  # isort:skip
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
from waste_collection_schedule.source_shell import SourceShell  # isort:skip
from custom_components.waste_collection_schedule.config_flow import (  # isort:skip
    WasteCollectionConfigFlow,
    WasteCollectionOptionsFlow,
    _build_schema_from_params,
    _is_new_style_source,
)
from custom_components.waste_collection_schedule.const import (  # isort:skip
    CONF_COLLECTION_TYPES,
    CONF_CUSTOMIZE,
    CONF_SENSORS,
    CONF_SOURCE_CALENDAR_TITLE,
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

    _, region_validator = _marker_and_validator(schema, "region")
    _, flag_validator = _marker_and_validator(schema, "flag")

    assert isinstance(region_validator, SelectSelector)
    assert isinstance(flag_validator, BooleanSelector)

    # Every member of an alternatives group is optional in the form (validate()
    # enforces that exactly one group is fully provided).
    #
    # Assert that through behaviour rather than `isinstance(marker, vol.Optional)`.
    # HA 2026.9 replaced voluptuous with probatio, whose
    # `probatio.compat.install_as_voluptuous()` re-points sys.modules["voluptuous"]
    # at a shim when `homeassistant` is first imported. This module binds `vol`
    # before importing homeassistant, so `vol.Optional` here stays the real
    # voluptuous class while config_flow builds `probatio.markers.Optional`
    # markers: an isinstance() check then compares two unrelated classes and
    # fails even though the markers are correct (and probatio markers repr as a
    # bare string, which made the failure read as if the key were un-wrapped).
    # Submitting subsets pins the same contract without caring which library
    # owns the marker type.
    assert schema({}) == {}
    assert schema({"region": "A"}) == {"region": "A"}
    assert schema({"flag": True}) == {"flag": True}


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


# --- #7142: a zero-argument pipeline source must render an empty form ---------
#
# koppl_at is one of the 20 pipeline sources that take no arguments at all, so
# each declares PARAMS = (). That is falsy, and the config flow decided "is this
# a pipeline source?" by testing PARAMS truthiness, so all 20 fell through to
# the legacy __init__-introspection path. A pipeline source has no __init__ of
# its own, so introspection found BaseSource.__init__(self, **kwargs) and the
# form offered a single text box literally named "kwargs".


class _StubHass:
    """The slice of HomeAssistant that __get_arg_schema actually touches."""

    class config:
        language = "en"

    @staticmethod
    async def async_add_executor_job(func, *args):
        return func(*args)


def _arg_schema(source: str, include_title: bool = True) -> vol.Schema:
    """Build the real config-flow argument schema for ``source``."""
    flow = WasteCollectionConfigFlow()
    flow.hass = cast(Any, _StubHass())
    schema, _module = asyncio.run(
        # Name-mangled private method: this is the code path the form is built
        # from, and the branch under test lives inside it.
        flow._WasteCollectionConfigFlow__get_arg_schema(  # type: ignore[attr-defined]
            source, {}, None, include_title
        )
    )
    return schema


def _field_names(schema: vol.Schema) -> set[str]:
    return {str(getattr(marker, "schema", marker)) for marker in schema.schema}


def test_a_zero_argument_pipeline_source_is_recognised_as_new_style() -> None:
    module = importlib.import_module("waste_collection_schedule.source.koppl_at")

    assert module.Source.PARAMS == ()  # falsy, which is what caused #7142
    assert _is_new_style_source(module.Source)


def test_a_legacy_source_is_not_recognised_as_new_style() -> None:
    module = importlib.import_module("waste_collection_schedule.source.static")

    assert not _is_new_style_source(module.Source)


def test_a_zero_argument_pipeline_source_renders_no_argument_fields() -> None:
    schema = _arg_schema("koppl_at")

    # The calendar title is the only thing to fill in; there are no arguments.
    assert _field_names(schema) == {CONF_SOURCE_CALENDAR_TITLE}


def test_a_zero_argument_pipeline_source_accepts_the_empty_form() -> None:
    schema = _arg_schema("koppl_at", include_title=False)

    assert _field_names(schema) == set()
    assert schema({}) == {}

    # ...and the flow builds the source from that empty submission.
    module = importlib.import_module("waste_collection_schedule.source.koppl_at")
    instance = WasteCollectionConfigFlow()._get_source_instance(module, {})

    assert instance.params == {}


def test_an_entry_stored_before_the_fix_still_loads() -> None:
    # Anyone who added one of these sources through the broken form has
    # {"kwargs": ...} sitting in their entry's source args. validate() only
    # checks the fields a source declares and ignores the rest, so the stray
    # value is inert: the entry still constructs and no migration is needed.
    shell = SourceShell.create("koppl_at", {}, {"kwargs": ""})

    assert shell is not None


# --- #7444: the customize selection offers the provider's original labels ----


def _raw_label_entries():
    import datetime

    from waste_collection_schedule import Collection

    d = datetime.date(2030, 1, 1)
    carried = Collection(d, "Restmuell")
    carried.set_description_from_raw_label("Container Restmuell")
    genuine = Collection(d, "Papier")
    genuine.set_description("Real ICS DESCRIPTION")
    return [carried, genuine]


class _FakeSource:
    def fetch(self):
        return _raw_label_entries()


def _shell(show_original_label: bool) -> SourceShell:
    return SourceShell(
        source=_FakeSource(),
        customize={},
        title="t",
        description="d",
        url=None,
        calendar_title=None,
        unique_id="u",
        day_offset=0,
        show_original_label=show_original_label,
    )


def test_shell_exposes_raw_labels_but_not_genuine_descriptions() -> None:
    for show in (True, False):
        shell = _shell(show)
        assert shell.raw_labels == []
        assert shell.fetch()
        # Recorded before the description is cleared, so it survives
        # show_original_label=False; a genuine description is never included.
        assert shell.raw_labels == ["Container Restmuell"]


def test_options_customize_dropdown_includes_raw_labels_not_sensors() -> None:
    from custom_components.waste_collection_schedule import const
    from custom_components.waste_collection_schedule.config_flow import (
        WCSCoordinator,
    )

    shell = _shell(False)
    shell.fetch()

    coordinator = object.__new__(WCSCoordinator)
    coordinator._shell = shell  # type: ignore[attr-defined]
    coordinator._aggregator = type(  # type: ignore[attr-defined]
        "_Agg", (), {"types": {"Restmuell", "Papier"}}
    )()

    from types import SimpleNamespace

    entry = SimpleNamespace(entry_id="e1", options={}, data={})
    hass = SimpleNamespace(
        config=SimpleNamespace(language="en"),
        data={const.DOMAIN: {"e1": coordinator}},
    )

    flow = object.__new__(WasteCollectionOptionsFlow)
    flow._entry = cast(Any, entry)
    flow.hass = cast(Any, hass)

    result = asyncio.run(flow.async_step_init())
    schema = result["data_schema"]
    selector = next(
        v for k, v in schema.schema.items() if str(k.schema) == "customize_select"
    )
    values = {o["value"] for o in selector.config["options"]}
    assert "Container Restmuell" in values
    assert "Real ICS DESCRIPTION" not in values
    assert {"Restmuell", "Papier"} <= values

    # Sensor types come from the aggregator only: no raw labels.
    assert "Container Restmuell" not in flow.get_types_of_sensors_and_customizations()


# --- default sensors are optional and combine with custom sensors --------------


def _finish_options(create_default: bool | None, custom: list[dict]) -> list[dict]:
    flow = object.__new__(WasteCollectionConfigFlow)
    flow._title = "t"
    flow._args_data = {}
    flow._options = {CONF_SENSORS: custom} if custom else {}
    flow._auto_sensor_types = ["Paper", "Glass"]
    if create_default is not None:
        flow._create_default_sensors = create_default
    captured: dict[str, Any] = {}

    def _create_entry(**kwargs: Any) -> dict:
        captured.update(kwargs)
        return kwargs

    flow.async_create_entry = _create_entry  # type: ignore[method-assign]
    asyncio.run(flow.finish())
    return captured["options"].get(CONF_SENSORS, [])


def test_default_sensors_are_created_by_default() -> None:
    assert [s[CONF_NAME] for s in _finish_options(None, [])] == ["Paper", "Glass"]


def test_default_sensors_can_be_switched_off() -> None:
    assert _finish_options(False, []) == []


def test_default_sensors_are_added_next_to_custom_sensors() -> None:
    custom = [{CONF_NAME: "Mine", CONF_COLLECTION_TYPES: ["Paper"]}]
    names = [s[CONF_NAME] for s in _finish_options(True, custom)]
    assert names == ["Mine", "Paper", "Glass"]


def test_custom_sensors_only_when_defaults_are_off() -> None:
    custom = [{CONF_NAME: "Mine", CONF_COLLECTION_TYPES: ["Paper"]}]
    assert [s[CONF_NAME] for s in _finish_options(False, custom)] == ["Mine"]


def test_a_custom_sensor_named_like_a_type_replaces_that_default() -> None:
    custom = [{CONF_NAME: "Paper", CONF_COLLECTION_TYPES: ["Paper"]}]
    names = [s[CONF_NAME] for s in _finish_options(True, custom)]
    assert names == ["Paper", "Glass"]
