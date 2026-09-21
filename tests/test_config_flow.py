import asyncio
import calendar  # noqa: F401 — must import stdlib calendar FIRST
import importlib
import os
import sys
import types

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

from typing import Any, cast

from collections.abc import Mapping  # isort:skip

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
    CONF_SENSOR_MODE,
    CONF_SENSORS,
    CONF_SOURCE_CALENDAR_TITLE,
    SENSOR_MODE_DAYS_TO,
    SENSOR_MODE_LAST_UPDATE,
)
from custom_components.waste_collection_schedule.default_sensors import (  # isort:skip
    DAYS_TO_NAME,
    KIND_LEGACY,
    KIND_NEW,
    LAST_UPDATE_NAME,
    NEW_SENSOR_NAMES,
    NEXT_COLLECTION_NAME,
    build_default_sensors,
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

    result = cast(dict[str, Any], schema({"count": 5.0}))

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
    schema = result.get("data_schema")
    assert schema is not None
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


def _finish_options(kinds: list[str] | None, custom: list[dict]) -> list[dict]:
    flow = object.__new__(WasteCollectionConfigFlow)
    flow._title = "t"
    flow._args_data = {}
    flow._options = {CONF_SENSORS: custom} if custom else {}
    flow._auto_sensor_types = ["Paper", "Glass"]
    if kinds is not None:
        flow._default_sensor_kinds = kinds
    captured: dict[str, Any] = {}

    def _create_entry(**kwargs: Any) -> dict:
        captured.update(kwargs)
        return kwargs

    flow.async_create_entry = _create_entry  # type: ignore[method-assign]
    asyncio.run(flow.finish())
    return captured["options"].get(CONF_SENSORS, [])


def test_both_default_sets_are_created_by_default() -> None:
    assert [s[CONF_NAME] for s in _finish_options(None, [])] == [
        "Paper",
        "Glass",
        *NEW_SENSOR_NAMES,
    ]


def test_only_the_legacy_default_sensors() -> None:
    assert [s[CONF_NAME] for s in _finish_options([KIND_LEGACY], [])] == [
        "Paper",
        "Glass",
    ]


def test_only_the_new_default_sensors() -> None:
    assert [s[CONF_NAME] for s in _finish_options([KIND_NEW], [])] == list(
        NEW_SENSOR_NAMES
    )


def test_default_sensors_can_be_switched_off() -> None:
    assert _finish_options([], []) == []


def test_default_sensors_are_added_next_to_custom_sensors() -> None:
    custom = [{CONF_NAME: "Mine", CONF_COLLECTION_TYPES: ["Paper"]}]
    names = [s[CONF_NAME] for s in _finish_options([KIND_LEGACY], custom)]
    assert names == ["Mine", "Paper", "Glass"]


def test_custom_sensors_only_when_defaults_are_off() -> None:
    custom = [{CONF_NAME: "Mine", CONF_COLLECTION_TYPES: ["Paper"]}]
    assert [s[CONF_NAME] for s in _finish_options([], custom)] == ["Mine"]


def test_a_custom_sensor_named_like_a_type_replaces_that_default() -> None:
    custom = [{CONF_NAME: "Paper", CONF_COLLECTION_TYPES: ["Paper"]}]
    names = [s[CONF_NAME] for s in _finish_options([KIND_LEGACY], custom)]
    assert names == ["Paper", "Glass"]


# ---------------------------------------------------------------------------
# cascading_select: one level per view
#
# The whole cascade used to live on the single argument form. Only the widest
# level could be populated up front — every deeper level needs the choices above
# it — so the rest rendered as free text and the user had to submit an
# incomplete form, and read the validation error it produced, once per level
# just to reveal the next dropdown (#7419).
# ---------------------------------------------------------------------------


def _register_cascade_source(name: str, choices, levels=("one", "two", "three")):
    """Install a throwaway cascading_select source under ``name``.

    ``choices`` is called as ``choices(field, selections)``; raising from it
    stands in for an unreachable provider.
    """
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.config_params import cascading_select

    class _Source(BaseSource):
        TITLE = name
        PARAMS = (cascading_select(*levels),)

        @classmethod
        def get_choices(cls, field, selections):
            return choices(field, selections)

    module = types.ModuleType(f"waste_collection_schedule.source.{name}")
    module.Source = _Source  # type: ignore[attr-defined]
    sys.modules[f"waste_collection_schedule.source.{name}"] = module
    return module


def _cascade_flow(source_name: str):
    """A flow parked on ``source_name``, with async_show_form captured."""
    flow = WasteCollectionConfigFlow()
    flow.hass = cast(Any, _StubHass())
    flow._source = source_name
    flow._id = source_name
    flow._extra_info_default_params = {}
    shown: list[dict] = []

    def _show_form(**kwargs):
        shown.append(kwargs)
        return kwargs

    flow.async_show_form = _show_form  # type: ignore[method-assign]
    return flow, shown


def _shown_fields(form: Mapping) -> list[str]:
    return [
        str(getattr(marker, "schema", marker)) for marker in form["data_schema"].schema
    ]


def test_a_cascade_asks_for_one_level_per_view() -> None:
    picked = {"one": "A", "two": "B", "three": "C"}

    def choices(field, selections):
        # Mirrors the contract: a level is only offered once everything above it
        # has been answered.
        levels = ["one", "two", "three"]
        for level in levels:
            if level == field:
                return [picked[level], "other"]
            if not selections.get(level):
                return []
        return []

    _register_cascade_source("cascade_happy", choices)
    flow, shown = _cascade_flow("cascade_happy")

    form = asyncio.run(flow.async_step_args())
    assert _shown_fields(form) == ["one"]

    form = asyncio.run(flow.async_step_args({"one": "A"}))
    assert _shown_fields(form) == ["two"]

    form = asyncio.run(flow.async_step_args({"two": "B"}))
    assert _shown_fields(form) == ["three"]

    # Answering the last level hands over to the ordinary argument form. The
    # settled levels are NOT offered again: re-opening "one" there would let a
    # user invalidate "two"/"three" underneath it with no way to notice.
    form = asyncio.run(flow.async_step_args({"three": "C"}))
    assert _shown_fields(form) == [CONF_SOURCE_CALENDAR_TITLE]
    assert flow._cascade_selections == picked
    assert len(shown) == 4

    # ...and they are shown as text instead, so the user still sees what the
    # entry is about to be created from. That view has its own step, whose
    # description is the address and nothing else — no "configure your service
    # provider" blurb, no source HOWTO, both already answered by the cascade.
    assert form.get("step_id") == "cascade_confirm"
    placeholders = form.get("description_placeholders")
    assert placeholders is not None
    assert list(placeholders) == ["cascade_summary"]
    description_placeholders = form.get("description_placeholders")
    assert description_placeholders is not None
    summary = description_placeholders["cascade_summary"]
    assert isinstance(summary, str)
    for level, value in picked.items():
        # A markdown list item per level: the description is rendered as
        # markdown, where bare newlines would run the levels into one line.
        assert f"- **{level.capitalize()}:** {value}" in summary
    assert len(summary.splitlines()) == len(picked)


def test_the_confirmation_step_is_translated() -> None:
    # It is a fixed step id, so it needs a hand-maintained entry in every
    # shipped language or the view renders with raw keys.
    import json
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / (
        "custom_components/waste_collection_schedule/translations"
    )
    for lang in ("en", "de", "fr", "it", "nl", "sl"):
        step = json.loads((base / f"{lang}.json").read_text(encoding="utf-8"))
        step = step["config"]["step"]["cascade_confirm"]
        assert step["description"] == "{cascade_summary}"
        assert step["data"][CONF_SOURCE_CALENDAR_TITLE]


def test_settled_cascade_levels_are_merged_back_into_the_submission() -> None:
    # They are not on the form, so nothing else would carry them into the entry.
    def choices(field, selections):
        levels = ["one", "two", "three"]
        for level in levels:
            if level == field:
                return ["A", "B", "C"]
            if not selections.get(level):
                return []
        return []

    _register_cascade_source("cascade_merge", choices)
    flow, _shown = _cascade_flow("cascade_merge")

    asyncio.run(flow.async_step_args())
    asyncio.run(flow.async_step_args({"one": "A"}))
    asyncio.run(flow.async_step_args({"two": "B"}))
    asyncio.run(flow.async_step_args({"three": "C"}))

    captured: dict = {}

    async def _validate(source, args_input, module):
        captured.update(args_input)
        return {}, {}, {}

    flow._WasteCollectionConfigFlow__validate_args_user_input = _validate  # type: ignore[attr-defined]
    flow.async_step_flow_type = lambda user_input=None: _done()  # type: ignore[method-assign]

    async def _done():
        return {"type": "done"}

    asyncio.run(flow.async_step_args({CONF_SOURCE_CALENDAR_TITLE: "Bins"}))

    assert captured["one"] == "A"
    assert captured["two"] == "B"
    assert captured["three"] == "C"


def test_a_cascade_level_with_no_options_is_skipped() -> None:
    # The cascading_select contract: a level that returns [] does not apply to
    # the current selection, so the wizard must step over it rather than
    # showing an empty dropdown.
    def choices(field, selections):
        if field == "one":
            return ["A"]
        if field == "two":
            return []  # not applicable
        return ["C"] if selections.get("one") else []

    _register_cascade_source("cascade_skips", choices)
    flow, _shown = _cascade_flow("cascade_skips")

    form = asyncio.run(flow.async_step_args())
    assert _shown_fields(form) == ["one"]

    form = asyncio.run(flow.async_step_args({"one": "A"}))
    assert _shown_fields(form) == ["three"]
    assert "two" not in flow._cascade_selections


def test_an_unreachable_cascade_falls_back_to_the_plain_form() -> None:
    # A dead provider must not dead-end the flow: the user still gets the
    # ordinary form (free text), which is what they had before the wizard.
    def choices(field, selections):
        raise RuntimeError("provider down")

    _register_cascade_source("cascade_down", choices)
    flow, _shown = _cascade_flow("cascade_down")

    form = asyncio.run(flow.async_step_args())

    assert set(_shown_fields(form)) == {
        CONF_SOURCE_CALENDAR_TITLE,
        "one",
        "two",
        "three",
    }


def test_a_source_without_a_cascade_still_gets_one_form() -> None:
    schema = _arg_schema("koppl_at")

    assert _field_names(schema) == {CONF_SOURCE_CALENDAR_TITLE}


def test_a_cascade_that_breaks_mid_way_keeps_what_was_answered() -> None:
    # Losing the levels already picked would send the user back to the start of
    # an address they had half-entered.
    def choices(field, selections):
        if field == "one":
            return ["A"]
        raise RuntimeError("provider down")

    _register_cascade_source("cascade_half", choices)
    flow, _shown = _cascade_flow("cascade_half")

    asyncio.run(flow.async_step_args())
    form = asyncio.run(flow.async_step_args({"one": "A"}))

    assert set(_shown_fields(form)) == {
        CONF_SOURCE_CALENDAR_TITLE,
        "one",
        "two",
        "three",
    }
    assert flow._extra_info_default_params == {"one": "A"}


def _settled_cascade(name: str):
    """A flow parked on the closing view, with all three levels answered."""

    def choices(field, selections):
        levels = ["one", "two", "three"]
        for level in levels:
            if level == field:
                return ["A", "B", "C"]
            if not selections.get(level):
                return []
        return []

    _register_cascade_source(name, choices)
    flow, shown = _cascade_flow(name)

    asyncio.run(flow.async_step_args())
    asyncio.run(flow.async_step_args({"one": "A"}))
    asyncio.run(flow.async_step_args({"two": "B"}))
    form = asyncio.run(flow.async_step_args({"three": "C"}))
    assert form.get("step_id") == "cascade_confirm"

    return flow, shown


def test_an_error_on_a_settled_level_re_opens_the_cascade() -> None:
    # The closing view has no input for a settled level, so an error naming one
    # would bind to a field that is not on the form: nothing renders, and the
    # user is asked to resubmit a form that never says what is wrong. The lists
    # can also go stale between the wizard reading them and the fetch, so this
    # is reachable however carefully the levels were picked.
    flow, _shown = _settled_cascade("cascade_stale")

    async def _validate(source, args_input, module):
        return (
            {"three": "invalid_arg"},
            {"invalid_arg_message": "no schedule for C"},
            {},
        )

    flow._WasteCollectionConfigFlow__validate_args_user_input = _validate  # type: ignore[attr-defined]

    form = asyncio.run(flow.async_step_args({CONF_SOURCE_CALENDAR_TITLE: "Bins"}))

    # Back on the ordinary argument form, with every level offered again - the
    # blamed one has to be changeable, and the levels above it decide what it
    # may be changed to.
    assert form.get("step_id") == "args_cascade_stale"
    assert set(_shown_fields(form)) == {
        CONF_SOURCE_CALENDAR_TITLE,
        "one",
        "two",
        "three",
    }
    assert form.get("errors") == {"three": "invalid_arg"}
    # invalid_arg's text is "Argument is invalid: {invalid_arg_message}", so the
    # placeholder has to survive the switch back to that step.
    description_placeholders = form.get("description_placeholders")
    assert description_placeholders is not None
    assert description_placeholders["invalid_arg_message"] == ("no schedule for C")
    # Still the user's own answers, not a blank form.
    assert flow._extra_info_default_params == {"one": "A", "two": "B", "three": "C"}


def test_an_error_elsewhere_keeps_the_closing_view() -> None:
    # Only an error the closing view cannot show re-opens the cascade. A fetch
    # error, or one naming a field that IS on the form, renders where it is and
    # must not throw the settled levels back at the user.
    flow, _shown = _settled_cascade("cascade_base_error")

    async def _validate(source, args_input, module):
        return {"base": "fetch_error"}, {"fetch_error_message": "boom"}, {}

    flow._WasteCollectionConfigFlow__validate_args_user_input = _validate  # type: ignore[attr-defined]

    form = asyncio.run(flow.async_step_args({CONF_SOURCE_CALENDAR_TITLE: "Bins"}))

    assert form.get("step_id") == "cascade_confirm"
    assert _shown_fields(form) == [CONF_SOURCE_CALENDAR_TITLE]
    assert form.get("errors") == {"base": "fetch_error"}


# ---------------------------------------------------------------------------
# The wizard is generic, so it also takes over the flow for the cascading_select
# sources that were already shipping. These drive it against the real ones,
# replaying each source's recorded get_choices walk (tests/fixtures/<source>/
# _choices.json), so the contract is checked against live-recorded provider
# responses rather than a synthetic stand-in.
# ---------------------------------------------------------------------------


def _walk_real_cascade(module_name: str, context: dict | None = None):
    """Run the wizard against a recorded source, answering as the walk records.

    Returns (fields asked one per view, final form).
    """
    import json

    import cassette  # tests/ is only on sys.path at runtime

    path = os.path.join(
        os.path.dirname(__file__), "fixtures", module_name, "_choices.json"
    )
    with open(path, encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta.get("widget") == "cascading_select"

    importlib.import_module(f"waste_collection_schedule.source.{module_name}")
    flow, _shown = _cascade_flow(module_name)
    # What the source needs but the cascade does not ask for: abfall_io keys
    # every lookup on `key`, which the user gets from the region they picked.
    flow._extra_info_default_params = dict(
        meta["context"] if context is None else context
    )

    asked: list[str] = []
    with cassette.replaying(path):
        form = asyncio.run(flow.async_step_args())
        for _ in range(len(meta["fields"]) + 1):
            fields = _shown_fields(form)
            # A cascade view is one dropdown and nothing else; anything wider is
            # the ordinary argument form, which ends the walk.
            if len(fields) != 1 or fields == [CONF_SOURCE_CALENDAR_TITLE]:
                break
            field = fields[0]
            asked.append(field)
            form = asyncio.run(
                flow.async_step_args({field: str(meta["expected"][field])})
            )

    return asked, form, meta


def test_the_wizard_walks_a_recorded_cascade_one_level_per_view() -> None:
    for module_name in ("kiedysmieci_info", "aw_harburg_de", "beachwood_oh_us"):
        asked, form, meta = _walk_real_cascade(module_name)

        # Every level the recording resolved was asked for on its own view, in
        # declaration order, and the walk ended on the confirmation.
        assert asked == [f for f in meta["fields"] if f in meta["expected"]], (
            module_name
        )
        assert form.get("step_id") == "cascade_confirm", module_name
        assert _shown_fields(form) == [CONF_SOURCE_CALENDAR_TITLE], module_name


def test_a_cascade_keyed_on_a_non_level_param_still_walks() -> None:
    # abfall_io (41 regions) and app_abfallplus_de (145) resolve nothing without
    # a param that is not a cascade level - the service `key` / `app_id` that
    # the region pre-fills. Passing get_choices only the levels made it return
    # [] at every step, so the wizard skipped itself and silently handed back
    # the old single form.
    asked, form, _meta = _walk_real_cascade("abfall_io")

    # f_id_kommune is absent because this recorded service fixes its kommune and
    # returns [] for that level, which the cascade contract says to skip.
    assert asked == ["f_id_bezirk", "f_id_strasse", "f_id_strasse_hnr"]
    assert form.get("step_id") == "cascade_confirm"

    # ...and without the key, every level returns [] - which is what the wizard
    # did with it before, and is why it has to be passed through.
    asked, form, _meta = _walk_real_cascade("abfall_io", context={})

    assert asked == []
    assert form.get("step_id") == "args_abfall_io"


def test_a_skipped_level_is_not_offered_on_the_closing_form() -> None:
    # A level that returns no options does not apply to this selection, and the
    # wizard steps over it. It is settled just as much as an answered one: left
    # on the closing form it comes back as an empty text box, offering exactly
    # what was stepped over (app_abfallplus_de skips bundesland/landkreis for
    # apps that fix them).
    def choices(field, selections):
        if field == "two":
            return []  # not applicable
        if field == "one":
            return ["A"]
        return ["C"] if selections.get("one") else []

    _register_cascade_source("cascade_skip_hidden", choices)
    flow, _shown = _cascade_flow("cascade_skip_hidden")

    asyncio.run(flow.async_step_args())
    form = asyncio.run(flow.async_step_args({"one": "A"}))
    assert _shown_fields(form) == ["three"]
    form = asyncio.run(flow.async_step_args({"three": "C"}))

    assert form.get("step_id") == "cascade_confirm"
    assert _shown_fields(form) == [CONF_SOURCE_CALENDAR_TITLE]
    assert "two" in flow._cascade_omitted()
    # ...and it contributes nothing to the entry, rather than an empty string.
    assert "two" not in flow._cascade_values()
    # Nor is it listed in the summary, where a blank line would read as
    # something the user failed to fill in.
    assert (
        "two"
        not in (
            (form.get("description_placeholders") or {}).get("cascade_summary") or ""
        ).lower()
    )


def test_a_skipped_level_keeps_a_value_the_region_pre_filled() -> None:
    # Skipping must not drop it: it is not asked for because it is already
    # decided, and the entry still needs it.
    def choices(field, selections):
        return ["A"] if field == "one" else []

    _register_cascade_source("cascade_skip_prefilled", choices)
    flow, _shown = _cascade_flow("cascade_skip_prefilled")
    flow._extra_info_default_params = {"two": "pinned"}

    asyncio.run(flow.async_step_args())
    asyncio.run(flow.async_step_args({"one": "A"}))

    assert flow._cascade_values() == {"one": "A", "two": "pinned"}


def test_an_inert_cascade_leaves_every_level_editable() -> None:
    # Every level inapplicable means the cascade never engaged - a source whose
    # lookup key is not known yet (abfall_io before `key`). Nothing is settled,
    # so hiding the levels would leave a form with no address fields at all.
    def choices(field, selections):
        return []

    _register_cascade_source("cascade_inert", choices)
    flow, _shown = _cascade_flow("cascade_inert")

    form = asyncio.run(flow.async_step_args())

    assert form.get("step_id") == "args_cascade_inert"
    assert set(_shown_fields(form)) == {
        CONF_SOURCE_CALENDAR_TITLE,
        "one",
        "two",
        "three",
    }


def test_the_summary_shows_labels_not_stored_values() -> None:
    # An option may be a (label, value) pair and it is the value that is stored,
    # so a summary built from the selections shows abfall_io's numeric ids where
    # the user picked a municipality by name.
    def choices(field, selections):
        levels = ["one", "two", "three"]
        for level in levels:
            if level == field:
                return [(f"{level.capitalize()} Name", f"{level}-id-42")]
            if not selections.get(level):
                return []
        return []

    _register_cascade_source("cascade_labels", choices)
    flow, _shown = _cascade_flow("cascade_labels")

    asyncio.run(flow.async_step_args())
    asyncio.run(flow.async_step_args({"one": "one-id-42"}))
    asyncio.run(flow.async_step_args({"two": "two-id-42"}))
    form = asyncio.run(flow.async_step_args({"three": "three-id-42"}))

    description_placeholders = form.get("description_placeholders")
    assert description_placeholders is not None
    summary = description_placeholders["cascade_summary"]
    assert isinstance(summary, str)
    for level in ("one", "two", "three"):
        assert f"{level.capitalize()} Name" in summary
        assert f"{level}-id-42" not in summary
    # The stored value is still what reaches the entry.
    assert flow._cascade_values() == {
        "one": "one-id-42",
        "two": "two-id-42",
        "three": "three-id-42",
    }


def test_the_closing_step_labels_every_field_it_can_show() -> None:
    # cascade_confirm is a fixed step id, so its labels are hand-maintained
    # while args_<id> is generated. Any non-cascade param of a cascading source
    # can appear on that form (stadt_kerpen_de's waste-type selection is the
    # case that shows it), and an unlabelled field renders as its raw name.
    # Computed from the sources so a new cascading source cannot quietly add a
    # param that loses its label.
    import json
    from pathlib import Path

    from waste_collection_schedule.source import __path__ as source_path

    extras = {CONF_SOURCE_CALENDAR_TITLE}
    for module_path in sorted(Path(source_path[0]).glob("*.py")):
        if module_path.stem.startswith("_"):
            continue
        try:
            module = importlib.import_module(
                f"waste_collection_schedule.source.{module_path.stem}"
            )
        except Exception:
            continue
        params = getattr(getattr(module, "Source", None), "PARAMS", None)
        if not params or not any(p.widget == "cascading_select" for p in params):
            continue
        extras.update(
            field
            for param in params
            if param.widget != "cascading_select"
            for field in param.fields
        )

    base = Path(__file__).resolve().parent.parent / (
        "custom_components/waste_collection_schedule/translations"
    )
    for lang in ("en", "de", "fr", "it", "nl", "sl"):
        labels = json.loads((base / f"{lang}.json").read_text(encoding="utf-8"))
        labels = labels["config"]["step"]["cascade_confirm"]["data"]
        missing = sorted(extras - set(labels))
        assert not missing, (
            f"{lang}.json: cascade_confirm.data has no label for {missing}. "
            "The closing view can show these, and an unlabelled field renders "
            "as its raw field name. Add them by hand - the args_* sections are "
            "generated, this one is not."
        )


def _options_flow(existing: list[dict]) -> tuple[WasteCollectionOptionsFlow, dict]:
    """An options flow of an existing entry that already has ``existing`` sensors."""
    from types import SimpleNamespace

    from custom_components.waste_collection_schedule import const
    from custom_components.waste_collection_schedule.config_flow import (
        WCSCoordinator,
    )

    coordinator = object.__new__(WCSCoordinator)
    coordinator._shell = cast(  # type: ignore[attr-defined]
        Any, SimpleNamespace(calendar_title="Calendar", raw_labels=[])
    )
    coordinator._aggregator = type(  # type: ignore[attr-defined]
        "_Agg", (), {"types": {"Restmuell", "Papier"}}
    )()
    entry = SimpleNamespace(
        entry_id="e1", options={CONF_SENSORS: existing} if existing else {}, data={}
    )
    hass = SimpleNamespace(
        config=SimpleNamespace(language="en"),
        data={const.DOMAIN: {"e1": coordinator}},
    )
    flow = object.__new__(WasteCollectionOptionsFlow)
    flow._entry = cast(Any, entry)
    flow.hass = cast(Any, hass)
    saved: dict[str, Any] = {}

    def _create_entry(**kwargs: Any) -> dict:
        saved.update(kwargs["data"])
        return kwargs

    flow.async_create_entry = _create_entry  # type: ignore[method-assign]
    return flow, saved


def _submit_options(existing: list[dict], **extra: Any) -> dict:
    flow, saved = _options_flow(existing)
    form = {
        "calendar_title": "Calendar",
        "separator": ", ",
        "fetch_time": "01:00:00",
        "fetch_interval_days": 1,
        "random_fetch_time_offset": {"hours": 0, "minutes": 0, "seconds": 0},
        "day_switch_time": "10:00:00",
        "day_offset": 0,
        "ignore_duplicates": False,
        **extra,
    }
    asyncio.run(flow.async_step_init(form))
    # Picking a sensor to edit shows its form first, so nothing is saved yet:
    # the options built so far are what the next steps continue from.
    return saved or flow._options


def test_options_flow_adds_no_default_sensors_unless_asked() -> None:
    flow, _ = _options_flow([])
    result = asyncio.run(flow.async_step_init())
    assert "data_schema" in result
    schema = result["data_schema"]
    assert schema is not None
    marker, validator = _marker_and_validator(schema, "default_sensors")
    assert marker.default() == []  # opening the options changes nothing
    assert validator.config["multiple"] is True

    saved = _submit_options([{CONF_NAME: "Mine", CONF_COLLECTION_TYPES: ["Papier"]}])
    assert [s[CONF_NAME] for s in saved[CONF_SENSORS]] == ["Mine"]


def test_options_flow_adds_only_the_missing_default_sensors() -> None:
    per_type = build_default_sensors([KIND_LEGACY], ["Papier"])
    saved = _submit_options(per_type, default_sensors=[KIND_LEGACY, KIND_NEW])
    # Papier exists and stays untouched; the rest of the sets is added.
    assert [s[CONF_NAME] for s in saved[CONF_SENSORS]] == [
        "Papier",
        "Restmuell",
        *NEW_SENSOR_NAMES,
    ]
    assert saved[CONF_SENSORS][0] == per_type[0]
    assert "default_sensors" not in saved  # a choice, not a stored option


def test_options_flow_does_not_duplicate_a_sensor_picked_for_editing() -> None:
    existing = build_default_sensors([KIND_NEW], [])
    saved = _submit_options(
        existing, default_sensors=[KIND_NEW], sensor_select=[NEXT_COLLECTION_NAME]
    )
    # The sensor is being edited (removed and re-added by the next step), so
    # ticking the set must not add a second one under the same name.
    assert [s[CONF_NAME] for s in saved[CONF_SENSORS]] == [
        DAYS_TO_NAME,
        LAST_UPDATE_NAME,
    ]


def test_editing_an_overview_sensor_keeps_its_mode() -> None:
    existing = build_default_sensors([KIND_NEW], [])
    flow, saved = _options_flow(existing)
    form = {
        "calendar_title": "Calendar",
        "separator": ", ",
        "fetch_time": "01:00:00",
        "fetch_interval_days": 1,
        "random_fetch_time_offset": {"hours": 0, "minutes": 0, "seconds": 0},
        "day_switch_time": "10:00:00",
        "day_offset": 0,
        "ignore_duplicates": False,
        "sensor_select": [DAYS_TO_NAME],
    }
    asyncio.run(flow.async_step_init(form))
    # The sensor form has no mode field: submitting it must not turn the
    # sensor into a plain one.
    asyncio.run(flow.async_step_sensor({CONF_NAME: DAYS_TO_NAME}))

    edited = next(s for s in saved[CONF_SENSORS] if s[CONF_NAME] == DAYS_TO_NAME)
    assert edited[CONF_SENSOR_MODE] == SENSOR_MODE_DAYS_TO


def _flow_type_schema_and_choice(submitted: dict | None):
    flow = object.__new__(WasteCollectionConfigFlow)
    flow._title = "t"
    flow._args_data = {}
    flow._options = {}
    flow._auto_sensor_types = ["Paper"]
    captured: dict[str, Any] = {}

    def _show_form(**kwargs: Any) -> dict:
        captured["schema"] = kwargs["data_schema"]
        return kwargs

    def _create_entry(**kwargs: Any) -> dict:
        captured["options"] = kwargs["options"]
        return kwargs

    flow.async_show_form = _show_form  # type: ignore[method-assign]
    flow.async_create_entry = _create_entry  # type: ignore[method-assign]
    asyncio.run(flow.async_step_flow_type(submitted))
    return captured


def test_flow_type_offers_both_default_sets_preselected() -> None:
    schema = _flow_type_schema_and_choice(None)["schema"]
    marker, validator = _marker_and_validator(schema, "default_sensors")
    assert marker.default() == [KIND_LEGACY, KIND_NEW]
    assert validator.config["multiple"] is True
    assert validator.config["translation_key"] == "default_sensors"


def test_flow_type_choice_decides_which_default_sets_are_created() -> None:
    def names(submitted: dict) -> list[str]:
        options = _flow_type_schema_and_choice(submitted)["options"]
        return [s[CONF_NAME] for s in options.get(CONF_SENSORS, [])]

    assert names({"default_sensors": [KIND_NEW]}) == list(NEW_SENSOR_NAMES)
    assert names({"default_sensors": []}) == []
    assert names({}) == ["Paper", *NEW_SENSOR_NAMES]  # untouched = both


# --- build_default_sensors: one place decides what a default sensor is ---------


def test_legacy_default_sensors_keep_their_exact_shape() -> None:
    assert build_default_sensors([KIND_LEGACY], ["Paper"]) == [
        {
            CONF_NAME: "Paper",
            "details_format": "upcoming",
            CONF_COLLECTION_TYPES: ["Paper"],
            "value_template": 'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}',
        }
    ]


def test_no_kind_builds_no_default_sensors() -> None:
    assert build_default_sensors([], ["Paper", "Glass"]) == []


def test_new_defaults_are_the_three_overview_sensors_over_all_types() -> None:
    from jinja2 import Environment  # isort:skip

    sensors = {s[CONF_NAME]: s for s in build_default_sensors([KIND_NEW], ["Paper"])}
    assert list(sensors) == list(NEW_SENSOR_NAMES)
    assert NEXT_COLLECTION_NAME == "Next collection"
    for sensor in sensors.values():
        assert CONF_COLLECTION_TYPES not in sensor  # no filter: every type counts
        assert sensor["details_format"] == "hidden"

    # Syntax only: HA's cv.template needs a running event loop on current HA.
    Environment().parse(sensors[NEXT_COLLECTION_NAME]["value_template"])
    assert CONF_SENSOR_MODE not in sensors[NEXT_COLLECTION_NAME]
    assert sensors[DAYS_TO_NAME][CONF_SENSOR_MODE] == SENSOR_MODE_DAYS_TO
    assert sensors[LAST_UPDATE_NAME][CONF_SENSOR_MODE] == SENSOR_MODE_LAST_UPDATE


def test_new_defaults_do_not_depend_on_the_fetched_types() -> None:
    assert [s[CONF_NAME] for s in build_default_sensors([KIND_NEW], [])] == list(
        NEW_SENSOR_NAMES
    )


def test_legacy_and_new_defaults_combine() -> None:
    names = [
        s[CONF_NAME]
        for s in build_default_sensors([KIND_LEGACY, KIND_NEW], ["Paper", "Glass"])
    ]
    assert names == ["Paper", "Glass", *NEW_SENSOR_NAMES]


def test_an_existing_overview_sensor_is_not_duplicated() -> None:
    existing = [{CONF_NAME: NEXT_COLLECTION_NAME}]
    names = [s[CONF_NAME] for s in build_default_sensors([KIND_NEW], [], existing)]
    assert names == [DAYS_TO_NAME, LAST_UPDATE_NAME]  # only the missing ones


def test_building_defaults_twice_never_duplicates_a_sensor() -> None:
    first = build_default_sensors([KIND_LEGACY], ["Paper", "Glass"])
    assert build_default_sensors([KIND_LEGACY], ["Paper", "Glass"], first) == []
