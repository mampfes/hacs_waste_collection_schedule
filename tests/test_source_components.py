import os
import sys
from collections.abc import Iterable
from functools import cache
from importlib import import_module
from inspect import Parameter, signature
from types import GeneratorType, ModuleType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # isort:skip
from update_docu_links import (  # isort:skip
    BLACK_LIST,
    COUNTRYCODES,
    LANGUAGES,
)

SOURCES_NO_COUNTRY = [g.split("/")[-1].removesuffix(".md") for g in BLACK_LIST]
SOURCES_TO_EXCLUDE = ["__init__.py", "example.py"]
SOURCES_EXCLUDE_TEST_CASE_CHECK = ["multiple"]


def _uses_base_source_init(source_cls: type) -> bool:
    """Return True for new-style sources relying on BaseSource.__init__(**kwargs).

    Such sources accept their constructor kwargs through the inherited base
    __init__, so the valid/mandatory parameter names come from PARAMS rather
    than the (``**kwargs``-only) signature.
    """
    try:
        from waste_collection_schedule.base_source import BaseSource
    except Exception:
        return False
    return (
        isinstance(source_cls, type)
        and issubclass(source_cls, BaseSource)
        and getattr(source_cls, "__init__", None) is BaseSource.__init__
    )


EXTRA_INFO_TYPES: dict[str, type] = {
    "title": str,
    "url": str,
    "country": str,
    "default_params": dict,
}
EXTRA_INFO_KEYS = list(EXTRA_INFO_TYPES.keys())


SOURCE_PATH = os.path.join(
    os.path.dirname(__file__),
    "../custom_components/waste_collection_schedule/waste_collection_schedule/source",
)
SOURCE_MD_PATH = os.path.join(os.path.dirname(__file__), "../doc/source/")
ICS_YAML_PATH = os.path.join(os.path.dirname(__file__), "../doc/ics/yaml")
ICS_MD_PATH = os.path.join(os.path.dirname(__file__), "../doc/ics")


def _get_module(source: str) -> ModuleType:
    sys.path.append(
        os.path.join(
            os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
        )
    )
    return import_module(f"waste_collection_schedule.source.{source}")


ICS_MODULE = _get_module("ics")


@cache
def _get_sources() -> list[str]:
    sources = []
    for file in os.listdir(SOURCE_PATH):
        if file.endswith(".py") and file not in SOURCES_TO_EXCLUDE:
            sources.append(file[:-3])
            print(file)
    return sources


@cache
def _get_source_md() -> list[str]:
    sources = []
    for file in os.listdir(SOURCE_MD_PATH):
        if file.endswith(".md"):
            sources.append(file[:-3])
    return sources


@cache
def _get_ics_sources() -> list[str]:
    sources = []
    for file in os.listdir(ICS_YAML_PATH):
        if file.endswith(".yaml"):
            sources.append(file[:-5])
    return sources


@cache
def _get_ics_md() -> list[str]:
    sources = []
    for file in os.listdir(ICS_MD_PATH):
        if file.endswith(".md"):
            sources.append(file[:-3])
    return sources


@cache
def _load_ics_yaml(source: str) -> Any:
    with open(os.path.join(ICS_YAML_PATH, f"{source}.yaml"), encoding="utf-8") as file:
        return yaml.safe_load(file)


_SENTINEL = object()


def _source_meta(module: ModuleType, name: str, default=_SENTINEL):
    """Resolve a source's metadata attribute.

    Legacy sources declare metadata (TITLE, URL, TEST_CASES, ...) at module
    level. New-style (BaseSource) sources declare it on the ``Source`` class.
    Look at the module first, then fall back to the class.
    """
    if hasattr(module, name):
        return getattr(module, name)
    source_cls = getattr(module, "Source", None)
    if source_cls is not None and getattr(source_cls, name, None):
        return getattr(source_cls, name)
    if default is _SENTINEL:
        raise AttributeError(name)
    return default


def _has_source_meta(module: ModuleType, name: str) -> bool:
    # A module-level declaration counts even when falsy: a deliberate
    # ``TITLE = None`` marks a deprecated legacy source and must still pass.
    # New-style sources declare metadata on the Source class.
    if hasattr(module, name):
        return True
    return bool(getattr(getattr(module, "Source", None), name, None))


def _is_supported_country_code(code: str) -> bool:
    return any(code == country["code"] for country in COUNTRYCODES)


def _has_supported_country_code(file: str) -> bool:
    if file.endswith(".py"):
        file.removesuffix(".py")
    code = file.split("_")[-1]
    return _is_supported_country_code(code)


def test_no_extra_source_mds() -> None:
    sources = _get_sources()
    source_md = _get_source_md()
    for source in source_md:
        assert source in sources, f"found orphaned source markdown file: {source}.md"


def test_no_extra_ics_mds() -> None:
    sources = _get_ics_sources()
    source_md = _get_ics_md()
    for source in source_md:
        assert source in sources, f"found orphaned ics markdown file: {source}.md"


def test_enfield_address_match_uses_whole_house_number() -> None:
    module = _get_module("enfield_gov_uk")
    normalized_input = module.Source._normalize_address("51 Example Road AB1 2CD")

    correct_candidate = {
        "ADDRESS": "51, EXAMPLE ROAD, EXAMPLE, AB1 2CD",
        "PAO_START_NUMBER": "51",
        "STREET_DESCRIPTION": "EXAMPLE ROAD",
        "POSTCODE_LOCATOR": "AB1 2CD",
    }
    embedded_candidate = {
        "ADDRESS": "1, EXAMPLE ROAD, EXAMPLE, AB1 2CD",
        "PAO_START_NUMBER": "1",
        "STREET_DESCRIPTION": "EXAMPLE ROAD",
        "POSTCODE_LOCATOR": "AB1 2CD",
    }

    assert module.Source._matches_address(normalized_input, correct_candidate)
    assert not module.Source._matches_address(normalized_input, embedded_candidate)


def _param_translation_check(
    source: str,
    translations: Any,
    init_params_names: Iterable[str],
    source_param_to_test: str = "translations",
) -> None:
    assert isinstance(translations, dict), (
        f"{source_param_to_test} must be a dictionary in {source}"
    )
    for lang, lang_translations in translations.items():
        assert lang in LANGUAGES, (
            f"unknown/unsupported language code {lang} in {source} {source_param_to_test}, must be one of {LANGUAGES}"
        )
        assert isinstance(lang_translations, dict), (
            f"{source_param_to_test} must be a dictionary in {source}"
        )
        for argument, argument_translation in lang_translations.items():
            assert isinstance(argument, str), (
                f"{source_param_to_test} keys must be strings in {source} for language {lang}"
            )
            assert isinstance(argument_translation, str), (
                f"{source_param_to_test} values must be strings in {source} for language {lang}"
            )
            assert argument in init_params_names, (
                f"{source_param_to_test} key {argument} for language {lang} not a valid parameter in Source class in {source}"
            )


def _test_case_check(
    name: Any,
    test_case: Any,
    source: str,
    init_params_names: Iterable[str],
    mandatory_init_params_names: Iterable[str],
) -> None:
    assert isinstance(name, str), f"test_case key must be a string in source {source}"
    assert isinstance(test_case, dict), (
        f"test_case value must be a dictionary in source {source}"
    )
    for test_case_param in test_case.keys():
        assert isinstance(test_case_param, str), (
            f"test_case keys must be strings in source {source}"
        )
        assert test_case_param in init_params_names, (
            f"test_case key {test_case_param} not a valid parameter in Source class in source {source}"
        )

    for param in mandatory_init_params_names:
        assert param in test_case.keys(), (
            f"missing mandatory parameter ({param}) in test_case '{name}' in source {source}"
        )


def _test_source_has_necessary_parameters_test_cases(
    module: ModuleType,
    source: str,
    init_params_names: Iterable[str],
    mandatory_init_params_names: Iterable[str],
) -> None:
    assert _has_source_meta(module, "TEST_CASES"), (
        f"missing test_cases in source {source}"
    )
    test_cases = _source_meta(module, "TEST_CASES")
    assert isinstance(test_cases, dict), (
        f"test_cases must be a dictionary in source {source}"
    )
    assert len(test_cases) > 0, f"test_cases must not be empty in source {source}"

    if source not in SOURCES_EXCLUDE_TEST_CASE_CHECK:
        for name, test_case in test_cases.items():
            _test_case_check(
                name, test_case, source, init_params_names, mandatory_init_params_names
            )


def _test_source_has_necessary_parameters_extra_info(
    extra_info: dict, source: str, init_params_names: Iterable[str]
) -> None:
    # check if callable

    if callable(extra_info):
        try:
            extra_info = extra_info()
        except Exception as e:
            raise AssertionError(
                f"EXTRA_INFO() function in source {source} failed with {e}"
            ) from e

        # check if is iterable (list, tupüle, set)
        assert isinstance(extra_info, (list, tuple, set, GeneratorType)), (
            f"EXTRA_INFO in source {source}, must be or return an iterable"
        )
        # check if all items are dictionaries
        for item in extra_info:
            assert isinstance(item, dict), (
                f"EXTRA_INFO in source {source}, must return a list of dictionaries, but at least one is not a dict"
            )
            assert "title" in item, (
                f"EXTRA_INFO in source {source}, must have a new title key in each dictionary"
            )
            assert isinstance(item["title"], str), (
                f"EXTRA_INFO in source {source}, must have a string title key in each dictionary"
            )

            for key in item.keys():
                assert isinstance(key, str), (
                    f"EXTRA_INFO in source {source}, must only have string keys in each dictionary"
                )
                assert key in EXTRA_INFO_KEYS, (
                    f"Found unknown key {key} in source {source}, must have only the following keys: {EXTRA_INFO_KEYS}"
                )
                assert isinstance(item[key], EXTRA_INFO_TYPES[key]), (
                    f"EXTRA_INFO in source {source}, key {key} must have type {EXTRA_INFO_TYPES[key]}"
                )

            if "country" in item:
                assert _is_supported_country_code(item["country"]), (
                    f"unsupported country code in source {source} in EXTRA_INFO"
                )
            if "default_params" in item:
                for key in item["default_params"].keys():
                    assert isinstance(key, str), (
                        f"EXTRA_INFO in source {source}, default_params keys must be strings"
                    )
                    assert key in init_params_names, (
                        f"EXTRA_INFO in source {source}, default_params key {key} not a valid parameter in Source class"
                    )


def test_source_has_necessary_parameters() -> None:
    sources = _get_sources()
    for source in sources:
        module = _get_module(source)
        assert hasattr(module, "Source"), f"missing Source class in source {source}"
        init_params = signature(module.Source.__init__).parameters
        if _uses_base_source_init(module.Source):
            # New-style source relying on BaseSource.__init__(**kwargs): the
            # accepted kwargs are the fields declared in PARAMS, and the
            # mandatory ones are those on required ConfigParams.
            init_params_names = set()
            mandatory_init_params_names = set()
            for cfg_param in getattr(module.Source, "PARAMS", []):
                init_params_names.update(cfg_param.fields.keys())
                if getattr(cfg_param, "required", True):
                    mandatory_init_params_names.update(cfg_param.fields.keys())
        else:
            init_params_names = set(init_params.keys()) - {"self"}
            mandatory_init_params_names = {
                name
                for name, param in init_params.items()
                if param.default is Parameter.empty
            } - {"self"}
        assert _has_source_meta(module, "TITLE"), f"missing TITLE in source {source}"
        assert _has_source_meta(module, "DESCRIPTION"), (
            f"missing DESCRIPTION in source {source}"
        )
        assert _has_source_meta(module, "URL"), f"missing URL in source {source}"

        _test_source_has_necessary_parameters_test_cases(
            module, source, init_params_names, mandatory_init_params_names
        )

        assert hasattr(module.Source, "fetch"), (
            f"missing fetch method in Source class of source {source}"
        )

        # If COUNTRY is declared it must be a valid code — update_docu_links.py uses
        # this value directly and silently orphans the source if it doesn't match.
        # New-style (BaseSource) sources declare COUNTRY on the class; legacy sources
        # declare it at module level. Validate whichever is present.
        declared_country = getattr(module, "COUNTRY", None) or getattr(
            module.Source, "COUNTRY", None
        )
        if declared_country:
            assert _is_supported_country_code(declared_country), (
                f"unsupported country code {declared_country!r} in source {source}"
            )

        if source not in SOURCES_NO_COUNTRY and not _has_supported_country_code(source):
            assert declared_country, (
                f"missing COUNTRY in source {source} or supported countrycode in filename"
            )

        # A source covers one or more regions. The typed REGIONS list is
        # canonical; a legacy EXTRA_INFO (class or module level) is adapted into
        # Regions at the boundary so validation works in Region terms only.
        from waste_collection_schedule.regions import from_extra_info

        region_list = getattr(module.Source, "REGIONS", None)
        if region_list:
            region_list = list(region_list() if callable(region_list) else region_list)
        else:
            legacy = getattr(module.Source, "EXTRA_INFO", None)
            if legacy is None:
                legacy = getattr(module, "EXTRA_INFO", None)
            region_list = from_extra_info(legacy) if legacy is not None else []
        for r in region_list:
            assert isinstance(r.title, str) and r.title, (
                f"a REGION in source {source} must have a non-empty string title"
            )
            assert isinstance(r.params, dict), (
                f"a REGION in source {source} must have a dict of params"
            )
            for key in r.params:
                assert key in init_params_names, (
                    f"REGION in source {source}: param {key} is not a valid Source parameter"
                )
            if r.country:
                assert _is_supported_country_code(r.country), (
                    f"unsupported country code in source {source} REGION"
                )

        if hasattr(module, "HOW_TO_GET_ARGUMENTS_DESCRIPTION"):
            assert isinstance(module.HOW_TO_GET_ARGUMENTS_DESCRIPTION, dict), (
                f"HOW_TO_GET_ARGUMENTS_DESCRIPTION must be a dictionary in {source}"
            )
            for key, value in module.HOW_TO_GET_ARGUMENTS_DESCRIPTION.items():
                assert key in LANGUAGES, (
                    f"HOW_TO_GET_ARGUMENTS_DESCRIPTION key {key} must be a valid/supported language code in {source}, must be one of {LANGUAGES}"
                )
                assert isinstance(value, str), (
                    f"HOW_TO_GET_ARGUMENTS_DESCRIPTION values must be strings in {source}"
                )

        if hasattr(module, "PARAM_TRANSLATIONS"):
            _param_translation_check(
                source,
                module.PARAM_TRANSLATIONS,
                init_params_names,
                "PARAM_TRANSLATIONS",
            )
        if hasattr(module, "PARAM_DESCRIPTIONS"):
            _param_translation_check(
                source,
                module.PARAM_DESCRIPTIONS,
                init_params_names,
                "PARAM_DESCRIPTIONS",
            )

        # SOURCE_CODEOWNERS lives at module level (legacy) or on the Source
        # class (pipeline sources). Validate whichever is present.
        source_cls = getattr(module, "Source", None)
        if hasattr(module, "SOURCE_CODEOWNERS") or hasattr(
            source_cls, "SOURCE_CODEOWNERS"
        ):
            owners = getattr(module, "SOURCE_CODEOWNERS", None)
            if owners is None:
                owners = getattr(source_cls, "SOURCE_CODEOWNERS", None)
            assert isinstance(owners, list), (
                f"SOURCE_CODEOWNERS must be a list in {source}, got {type(owners).__name__}"
            )
            for i, handle in enumerate(owners):
                assert isinstance(handle, str) and handle.strip(), (
                    f"SOURCE_CODEOWNERS[{i}] in {source} must be a non-empty string"
                )
                assert handle.strip().startswith("@"), (
                    f"SOURCE_CODEOWNERS[{i}] in {source} must start with '@' "
                    f"(got {handle!r}). Use the canonical @handle format."
                )


def test_ics_source_has_necessary_parameters():
    sources = _get_ics_sources()
    # ics.py is a BaseSource pipeline source relying on BaseSource.__init__
    # (**kwargs): its accepted/mandatory parameter names come from PARAMS, the
    # same fallback test_source_components.py's own structural test uses (see
    # _uses_base_source_init above).
    if _uses_base_source_init(ICS_MODULE.Source):
        init_params_names = set()
        mandatory_init_params_names = set()
        for cfg_param in getattr(ICS_MODULE.Source, "PARAMS", []):
            init_params_names.update(cfg_param.fields.keys())
            if getattr(cfg_param, "required", True):
                mandatory_init_params_names.update(cfg_param.fields.keys())
    else:
        init_params = signature(ICS_MODULE.Source.__init__).parameters
        init_params_names = set(init_params.keys()) - {"self"}
        mandatory_init_params_names = {
            name
            for name, param in init_params.items()
            if param.default is Parameter.empty
        } - {"self"}
    for source in sources:
        data = _load_ics_yaml(source)
        assert isinstance(data, dict), f"yaml file {source}.yaml must be a dictionary"
        assert "title" in data, f"missing title in yaml file {source}.yaml"
        assert "url" in data, f"missing url in yaml file {source}.yaml"
        assert "howto" in data, f"missing howto in yaml file {source}.yaml"
        assert isinstance(data["howto"], dict), (
            f"howto must be a dictionary in yaml file {source}.yaml"
        )
        assert "en" in data["howto"], (
            f"missing english howto translation in {source}.yaml"
        )
        for key, value in data["howto"].items():
            assert isinstance(key, str), f"howto keys must be strings in {source}.yaml"
            assert key in LANGUAGES, (
                f"howto key {key} must be a valid/supported language code in {source}.yaml, must be one of {LANGUAGES}"
            )
            assert isinstance(value, str), (
                f"howto values must be strings in {source}.yaml"
            )

        assert "test_cases" in data, f"missing test_cases in yaml file {source}.yaml"
        assert isinstance(data["test_cases"], dict), (
            f"test_cases must be a dictionary in yaml file {source}.yaml"
        )
        for name, test_case in data["test_cases"].items():
            _test_case_check(
                name,
                test_case,
                f"ICS:{source}",
                init_params_names,
                mandatory_init_params_names,
            )
        if "extra_info" in data:
            _test_source_has_necessary_parameters_extra_info(
                data["extra_info"], f"ICS:{source}", init_params_names
            )

        if "codeowners" in data:
            ics_owners = data["codeowners"]
            assert isinstance(ics_owners, list), (
                f"codeowners must be a list in ICS yaml {source}.yaml, got {type(ics_owners).__name__}"
            )
            for i, handle in enumerate(ics_owners):
                assert isinstance(handle, str) and handle.strip(), (
                    f"codeowners[{i}] in ICS yaml {source}.yaml must be a non-empty string"
                )
                assert handle.strip().startswith("@"), (
                    f"codeowners[{i}] in ICS yaml {source}.yaml must start with '@' "
                    f"(got {handle!r}). Use the canonical @handle format."
                )


# Sources permitted to use raw `mdi:*` string literals in their ICON_MAP.
# Every other source must use the `Icons` enum from `waste_collection_schedule`
# (see issue #2813 / canonical icon catalogue). The allowlist below is for
# sources whose ICON_MAP isn't a simple ``str -> str`` static dict — they build
# the mapping programmatically, use integer keys, nest dicts per region, etc.
# and the canonical-icons test skips them. Future contributors of such sources
# should add themselves here and explain why.
SOURCES_ALLOWED_RAW_ICONS: set[str] = {
    "api_golemio_cz",  # integer keys (Czech API trash-type IDs)
    "cbcity_nsw_gov_au",  # dynamic ICON_MAP construction
    "insert_it_de",  # nested {region: {waste_type: {icon, name}}} structure
    "landkreis_helmstedt_de",  # computed keys
    "potsdam_de",  # integer keys
    "wermelskirchen_de",  # dynamic ICON_MAP construction
    "woollahra_nsw_gov_au",  # dynamic ICON_MAP construction
}


def test_icon_map_uses_canonical_icons() -> None:
    """ICON_MAP values must be ``Icons`` enum members, not raw ``mdi:*`` strings.

    Sources in :data:`SOURCES_ALLOWED_RAW_ICONS` are exempt because they build
    ICON_MAP dynamically and the runtime values can't be statically classified.
    """
    from waste_collection_schedule import Icons

    sources = _get_sources()
    for source in sources:
        if source in SOURCES_ALLOWED_RAW_ICONS:
            continue
        module = _get_module(source)
        icon_map = getattr(module, "ICON_MAP", None)
        if icon_map is None:
            continue
        if not isinstance(icon_map, dict):
            continue
        for key, value in icon_map.items():
            assert isinstance(value, Icons), (
                f"ICON_MAP value for {key!r} in source {source} is "
                f"{value!r}, expected an Icons enum member. "
                "Use `from waste_collection_schedule import Icons` and "
                "reference e.g. Icons.GENERAL_WASTE — see "
                "custom_components/waste_collection_schedule/waste_collection_schedule/icons.py"
            )


def test_uk_cloud9_retriever_falls_back_to_secondary_domain() -> None:
    module = import_module("waste_collection_schedule.service.uk_cloud9_apps")
    requested_urls: list[str] = []

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, dict]:
            return {"wasteCollectionDates": {}}

    class _Session:
        def get(self, url: str, **kwargs) -> _Response:
            requested_urls.append(url)
            if "primary.example.invalid" in url:
                raise ConnectionError("SSL host mismatch")
            return _Response()

    class _Source:
        def __init__(self) -> None:
            self.params = {"uprn": "100070200377"}
            self.session = _Session()

    retriever = module.Cloud9Retriever(
        "rugby",
        uprn_field="uprn",
        api_domains=("https://primary.example.invalid", "https://secondary.example"),
    )
    payload = retriever(_Source())

    assert payload == {"wasteCollectionDates": {}}
    assert requested_urls == [
        "https://primary.example.invalid/rugby/citizenmobile/mobileapi/wastecollections/100070200377",
        "https://secondary.example/rugby/citizenmobile/mobileapi/wastecollections/100070200377",
    ]


def test_uk_cloud9_retriever_requires_api_domains() -> None:
    module = import_module("waste_collection_schedule.service.uk_cloud9_apps")

    try:
        module.Cloud9Retriever("rugby", api_domains=())
        raise AssertionError("Expected ValueError when no API domains are configured")
    except ValueError as err:
        assert "At least one API domain" in str(err)


def test_mzv_rotenburg_route_filter_without_location() -> None:
    """Route filtering works when the route label is only in the ICS summary.

    The BaseSource conversion uses parsers.ics_events + classify(); route info
    here lives in the summary (LOCATION is empty), so route_context falls back
    to the summary text. convert_events is patched to avoid the wall-clock
    (now .. now+365) event window — this exercises classify(), not icalevents.
    """
    import datetime

    from waste_collection_schedule.service.ICS import IcsEvent

    module = _get_module("mzv_rotenburg_bebra_de")

    events = [
        IcsEvent(datetime.date(2026, 1, 1), "Entsorgung Gelbe Tonne Route 1"),
        IcsEvent(datetime.date(2026, 1, 2), "Entsorgung Gelbe Tonne Route 2"),
        IcsEvent(datetime.date(2026, 1, 3), "Entsorgung Papier Route West"),
        IcsEvent(datetime.date(2026, 1, 4), "Entsorgung Papier Route Ost"),
        IcsEvent(datetime.date(2026, 1, 5), "Entsorgung Restabfall"),
    ]

    response = MagicMock()
    # parse() guards against a non-ICS body (unknown city); give it a valid feed.
    response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
    with (
        patch.object(module.Source, "retrieve", return_value=response),
        patch(
            "waste_collection_schedule.service.ICS.ICS.convert_events",
            return_value=events,
        ),
    ):
        entries = module.Source(
            city="rote", yellow_route="2", paper_route="Ost"
        ).fetch()

    assert [(entry.date.isoformat(), entry.waste_type.id) for entry in entries] == [
        ("2026-01-02", "recyclables"),
        ("2026-01-04", "paper"),
        ("2026-01-05", "general_waste"),
    ]


def test_koma_pl_resolves_house_number_and_parses_schedule() -> None:
    module = _get_module("koma_pl")

    posesje = [
        {"numer_posesji": "ND00050", "numer_domu": "4/1", "ulica": "Kanałowa"},
        {"numer_posesji": "1941", "numer_domu": "5", "ulica": "Kanałowa"},
    ]
    schedule = {
        "rok": "2026",
        "odbior": [
            {"data": "2026-01-07", "typ": "Bio"},
            {"data": "2026-01-15", "typ": "Zmieszane"},
            {"data": "bad-date", "typ": "Papier"},
        ],
    }

    class _Response:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return self._payload

    requested = []

    class _Session:
        def get(self, url, params=None, timeout=None):
            requested.append((url, params))
            if "apiharmonogram" in url:
                return _Response(schedule)
            return _Response(posesje)

    with patch.object(module.requests, "Session", lambda **kwargs: _Session()):
        entries = module.Source(
            gmina="Nowy Dwór Gdański",
            miejscowosc="Nowy Dwór Gdański",
            ulica="Kanałowa",
            numer_domu="5",
        ).fetch()

    # House number "5" must resolve to property id 1941 in the schedule request.
    assert any(
        params and params.get("value") == "Nowy Dwór Gdański/1941"
        for _, params in requested
    )
    # Valid dates parsed, invalid date skipped.
    assert [(entry.date.isoformat(), entry.type) for entry in entries] == [
        ("2026-01-07", "Bio"),
        ("2026-01-15", "Zmieszane"),
    ]


def test_esch_lu_requests_identity_encoding() -> None:
    module = _get_module("esch_lu")
    calls: list[tuple[str, dict[str, Any]]] = []

    class _Response:
        content = (
            b'<table id="garbage-table"><tr><td></td><td>Organique</td>'
            b"<td>mardi, 28 juillet 2026</td></tr></table>"
        )

        @staticmethod
        def raise_for_status() -> None:
            return None

    class _Session:
        def get(self, url: str, **kwargs: Any) -> _Response:
            calls.append((url, kwargs))
            return _Response()

    with patch.object(module, "get_legacy_session", return_value=_Session()):
        entries = module.Source(zone="A").fetch()

    assert [(entry.date.isoformat(), entry.type) for entry in entries] == [
        ("2026-07-28", "Organique")
    ]
    assert calls == [
        (
            "https://administration.esch.lu/dechets/",
            {
                "params": {"street": 0, "tour": "1"},
                "headers": {"Accept-Encoding": "identity"},
            },
        )
    ]


class _OpenCitiesResponse:
    def __init__(self, *, json_data=None, text="", json_error=False):
        self._json_data = json_data
        self.text = text
        self._json_error = json_error

    def raise_for_status(self) -> None:
        return None

    def json(self):
        if self._json_error:
            raise ValueError("invalid json")
        return self._json_data


class _OpenCitiesSession:
    def __init__(self, responder) -> None:
        self.calls: list[tuple[str, dict | None]] = []
        self.headers_sent: list[dict | None] = []
        self._responder = responder

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params))
        self.headers_sent.append(headers)
        return self._responder(url, params)


class _OpenCitiesSource:
    """The slice of a BaseSource the OpenCities components touch."""

    def __init__(self, responder, **params) -> None:
        self.session = _OpenCitiesSession(responder)
        self.params = params


def _opencities_module():
    return import_module("waste_collection_schedule.service.OpenCities")


def _services(html: str) -> _OpenCitiesResponse:
    return _OpenCitiesResponse(json_data={"success": True, "responseContent": html})


def _one_hit(hit_id: str = "abc") -> _OpenCitiesResponse:
    return _OpenCitiesResponse(json_data={"Items": [{"Id": hit_id}]})


def _oc_responder(items_response, services_response):
    """Answer the search with one response and wasteservices with another."""

    def responder(url, params):
        if "myarea/search" in url:
            return items_response
        return services_response

    return responder


def _oc_parse(html: str, **parser_args):
    module = _opencities_module()
    raw = module.OpenCitiesResult(_services(html), "address", "1 Main St")
    return module.OpenCitiesParser(**parser_args)(raw)


def _oc_geolocation_ids(source) -> list[str]:
    return [
        params["geolocationid"]
        for url, params in source.session.calls
        if "wasteservices" in url
    ]


def test_opencities_retriever_resolves_single_address_result() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(
            _OpenCitiesResponse(
                json_data={
                    "Items": [{"Id": "abc-123", "AddressSingleLine": "1 Main St"}]
                }
            ),
            _services("<p>none</p>"),
        ),
        address="1 Main St",
    )

    module.OpenCitiesRetriever("https://example.invalid")(source)

    assert _oc_geolocation_ids(source) == ["abc-123"]


def test_opencities_retriever_raises_ambiguous_with_suggestions_on_multiple_matches() -> (
    None
):
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _OpenCitiesResponse(
            json_data={
                "Items": [
                    {"Id": "a", "AddressSingleLine": "1 Main St, Northtown"},
                    {"Id": "b", "AddressSingleLine": "1 Main St, Southtown"},
                ]
            }
        ),
        address="1 Main St",
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid", strict_address_matching=True
    )

    try:
        retriever(source)
        raise AssertionError("Expected SourceArgAmbiguousWithSuggestions")
    except module.SourceArgAmbiguousWithSuggestions as err:
        assert list(err.suggestions) == [
            "1 Main St, Northtown",
            "1 Main St, Southtown",
        ]


def test_opencities_retriever_selects_exact_match_among_multiple_results() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(
            _OpenCitiesResponse(
                json_data={
                    "Items": [
                        {"Id": "a", "AddressSingleLine": "5 Other St, Southtown"},
                        {"Id": "b", "AddressSingleLine": "  1 main st, northtown  "},
                    ]
                }
            ),
            _services("<p>none</p>"),
        ),
        address="1 main st, northtown",
    )

    module.OpenCitiesRetriever("https://example.invalid", strict_address_matching=True)(
        source
    )

    assert _oc_geolocation_ids(source) == ["b"]


def test_opencities_retriever_trusts_top_search_result_by_default() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(
            _OpenCitiesResponse(
                json_data={
                    "Items": [
                        {"Id": "a", "AddressSingleLine": "1 Main St, Northtown"},
                        {"Id": "b", "AddressSingleLine": "1 Main St, Southtown"},
                    ]
                }
            ),
            _services("<p>none</p>"),
        ),
        address="1 Main St, Somewhere Else",
    )

    module.OpenCitiesRetriever("https://example.invalid")(source)

    # With strict_address_matching left at its default (False), the
    # highest-ranked result is used even though it doesn't textually match
    # the query -- avoids turning normal fuzzy-search hits (e.g. missing a
    # state abbreviation) into a hard "ambiguous" failure.
    assert _oc_geolocation_ids(source) == ["a"]


def test_opencities_retriever_holds_a_lone_hit_to_exact_match_when_asked() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _OpenCitiesResponse(
            json_data={"Items": [{"Id": "a", "AddressSingleLine": "2 Lake Ridge Lane"}]}
        ),
        address="2 Wallarah Rd",
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid",
        strict_address_matching=True,
        strict_single_result=True,
    )

    try:
        retriever(source)
        raise AssertionError("Expected SourceArgAmbiguousWithSuggestions")
    except module.SourceArgAmbiguousWithSuggestions as err:
        assert list(err.suggestions) == ["2 Lake Ridge Lane"]


def test_opencities_retriever_raises_not_found_on_empty_search() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _OpenCitiesResponse(json_data={"Items": []}),
        street_address="nowhere",
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid", address="street_address"
    )

    try:
        retriever(source)
        raise AssertionError("Expected SourceArgumentNotFound")
    except module.SourceArgumentNotFound as err:
        assert err.argument == "street_address"


def test_opencities_retriever_uses_searchfuzzy_and_maxresults_when_configured() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")), address="1 Main St"
    )

    module.OpenCitiesRetriever(
        "https://example.invalid", search_fuzzy=True, max_results=1
    )(source)

    url, params = source.session.calls[0]
    assert url == "https://example.invalid/api/v1/myarea/searchfuzzy"
    assert params == {"keywords": "1 Main St", "maxresults": 1}


def test_opencities_retriever_includes_page_link_param_when_configured() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")), address="1 Main St"
    )

    module.OpenCitiesRetriever("https://example.invalid", page_link="/some/page")(
        source
    )

    _, params = source.session.calls[-1]
    assert params is not None
    assert params["pageLink"] == "/some/page"


def test_opencities_retriever_composes_the_address_from_a_template() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")),
        street_number="13-15",
        street_name="Learmonth  St",
        suburb="Rooty Hill",
        post_code=2766,
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid",
        address=None,
        address_template="{street_number} {street_name}, {suburb} NSW {post_code}",
        argument="street_name",
    )

    result = retriever(source)

    _, params = source.session.calls[0]
    assert params == {"keywords": "13-15 Learmonth St, Rooty Hill NSW 2766"}
    assert result.argument == "street_name"
    assert result.value == "13-15 Learmonth St, Rooty Hill NSW 2766"


def test_opencities_retriever_applies_normalise_before_searching() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")),
        address="19 Potter Street, Craigieburn",
    )

    module.OpenCitiesRetriever(
        "https://example.invalid", normalise=lambda text: text.replace(",", "")
    )(source)

    assert source.session.calls[0][1] == {"keywords": "19 Potter Street Craigieburn"}


def test_opencities_retriever_sends_json_accept_unless_the_source_names_one() -> None:
    module = _opencities_module()

    default = module.OpenCitiesRetriever("https://example.invalid")
    named = module.OpenCitiesRetriever(
        "https://example.invalid", headers={"accept": "text/plain, */*"}
    )

    assert default.headers == {"Accept": "application/json"}
    assert named.headers == {"accept": "text/plain, */*"}


def test_opencities_retriever_sends_its_headers_on_every_request() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")), address="1 Main St"
    )

    module.OpenCitiesRetriever(
        "https://example.invalid", headers={"Referer": "https://example.invalid/page"}
    )(source)

    assert len(source.session.headers_sent) == 2
    for headers in source.session.headers_sent:
        assert headers is not None
        assert headers["Referer"] == "https://example.invalid/page"
        assert headers["Accept"] == "application/json"


def test_opencities_retriever_retries_once_on_stale_cached_geolocation_id() -> None:
    module = _opencities_module()
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
    )
    search_calls = {"count": 0}

    def responder(url, params):
        if "myarea/search" in url:
            search_calls["count"] += 1
            return _OpenCitiesResponse(json_data={"Items": [{"Id": "fresh-id"}]})
        # wasteservices: fail for the stale cached id, succeed for the fresh one
        if params.get("geolocationid") == "stale-id":
            return _OpenCitiesResponse(json_data={"success": False})
        return _services(html)

    source = _OpenCitiesSource(responder, address="1 Main St")
    retriever = module.OpenCitiesRetriever("https://example.invalid")
    retriever._resolved[source] = "stale-id"

    result = retriever(source)

    assert search_calls["count"] == 1
    assert _oc_geolocation_ids(source) == ["stale-id", "fresh-id"]
    assert [r["type"] for r in module.OpenCitiesParser()(result)] == ["General Waste"]
    assert retriever._resolved[source] == "fresh-id"


def test_opencities_retriever_searches_once_across_repeated_fetches() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")), address="1 Main St"
    )
    retriever = module.OpenCitiesRetriever("https://example.invalid")

    retriever(source)
    retriever(source)

    searches = [url for url, _ in source.session.calls if "myarea/search" in url]
    assert len(searches) == 1
    assert _oc_geolocation_ids(source) == ["abc", "abc"]


def test_opencities_retriever_bypasses_search_when_geolocation_id_given_directly() -> (
    None
):
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _services("<p>none</p>"), geolocation_id="abc"
    )

    result = module.OpenCitiesRetriever(
        "https://example.invalid", address=None, geolocation_id="geolocation_id"
    )(source)

    assert all("myarea/search" not in url for url, _ in source.session.calls)
    assert (result.argument, result.value) == ("geolocation_id", "abc")


def test_opencities_retriever_prefers_a_geolocation_id_over_the_address() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _services("<p>none</p>"),
        street_address="1 Main St",
        geolocation_id="abc",
    )

    module.OpenCitiesRetriever(
        "https://example.invalid",
        address="street_address",
        geolocation_id="geolocation_id",
    )(source)

    assert all("myarea/search" not in url for url, _ in source.session.calls)
    assert _oc_geolocation_ids(source) == ["abc"]


def test_opencities_retriever_needs_an_address_or_a_geolocation_id() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _services("<p>none</p>"),
        street_address=None,
        geolocation_id=None,
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid",
        address="street_address",
        geolocation_id="geolocation_id",
    )

    try:
        retriever(source)
        raise AssertionError("Expected SourceArgumentExceptionMultiple")
    except module.SourceArgumentExceptionMultiple as err:
        assert list(err.arguments) == ["street_address", "geolocation_id"]


def test_opencities_retriever_fires_warm_up_url_once_before_wasteservices_when_configured() -> (
    None
):
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _services("<p>none</p>"), geolocation_id="abc"
    )
    retriever = module.OpenCitiesRetriever(
        "https://example.invalid",
        address=None,
        geolocation_id="geolocation_id",
        warm_up_url="https://example.invalid/warm",
        warm_up_before="wasteservices",
    )

    retriever(source)
    retriever(source)

    warm_up_calls = [url for url, _ in source.session.calls if url.endswith("/warm")]
    assert len(warm_up_calls) == 1
    assert source.session.calls[0][0].endswith("/warm")


def test_opencities_retriever_fires_warm_up_url_before_search_by_default() -> None:
    module = _opencities_module()
    source = _OpenCitiesSource(
        _oc_responder(_one_hit(), _services("<p>none</p>")), address="1 Main St"
    )

    module.OpenCitiesRetriever(
        "https://example.invalid", warm_up_url="https://example.invalid/warm"
    )(source)

    assert source.session.calls[0][0] == "https://example.invalid/warm"


def test_opencities_retriever_does_not_warm_up_before_wasteservices_by_default() -> (
    None
):
    module = _opencities_module()
    source = _OpenCitiesSource(
        lambda url, params: _services("<p>none</p>"), geolocation_id="abc"
    )

    module.OpenCitiesRetriever(
        "https://example.invalid",
        address=None,
        geolocation_id="geolocation_id",
        warm_up_url="https://example.invalid/warm",
    )(source)

    assert all("/warm" not in url for url, _ in source.session.calls)


def test_opencities_retriever_falls_back_from_json_to_xml_search_response() -> None:
    module = _opencities_module()
    xml = (
        "<Results><PhysicalAddressSearchResult>"
        "<Id>xml-id</Id><AddressSingleLine>1 Main St</AddressSingleLine>"
        "</PhysicalAddressSearchResult></Results>"
    )
    source = _OpenCitiesSource(
        _oc_responder(
            _OpenCitiesResponse(json_error=True, text=xml), _services("<p>none</p>")
        ),
        address="1 Main St",
    )

    module.OpenCitiesRetriever("https://example.invalid")(source)

    assert _oc_geolocation_ids(source) == ["xml-id"]


def test_opencities_parser_parses_wasteservices_html_into_records() -> None:
    records = _oc_parse(
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Mon 01/02/2027</div>'
        '<div class="note">Collected fortnightly</div></article>'
        "<article><h3>Recycling</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )

    assert [(r["date"].isoformat(), r["type"], r["note"]) for r in records] == [
        ("2027-02-01", "General Waste", "Collected fortnightly"),
        ("2027-02-02", "Recycling", None),
    ]


def test_opencities_parser_does_not_double_count_nested_article_in_result_div() -> None:
    records = _oc_parse(
        '<div class="waste-services-result"><article><h3>General Waste</h3>'
        '<div class="next-service">Mon 01/02/2027</div></article></div>'
    )

    assert len(records) == 1


def test_opencities_parser_skips_entries_missing_next_service_date() -> None:
    records = _oc_parse(
        '<article><h3>General Waste</h3><div class="next-service"></div></article>'
        "<article><h3>Recycling</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )

    assert [r["type"] for r in records] == ["Recycling"]


def test_opencities_parser_filters_by_date_precise_class_when_configured() -> None:
    records = _oc_parse(
        '<div class="waste-services-result date-precise"><h3>General Waste</h3>'
        '<div class="next-service">Mon 01/02/2027</div></div>'
        '<div class="waste-services-result"><h3>Recycling</h3>'
        '<div class="next-service">Every fortnight</div></div>',
        require_date_precise=True,
    )

    assert [r["type"] for r in records] == ["General Waste"]


def test_opencities_parser_drops_excluded_type_prefixes() -> None:
    records = _oc_parse(
        "<article><h3>Calendar - GlassZone 8</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>',
        exclude_type_prefixes=("Calendar",),
    )

    assert [r["type"] for r in records] == ["General Waste"]


def test_opencities_parser_reads_a_custom_date_format() -> None:
    records = _oc_parse(
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Monday 01 February 2027</div></article>',
        date_format="%A %d %B %Y",
    )

    assert records[0]["date"].isoformat() == "2027-02-01"


def test_opencities_parser_resolves_every_weekday_recurring_text() -> None:
    from datetime import date as _date

    records = _oc_parse(
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Every Monday</div></article>'
    )

    assert len(records) == 1
    assert records[0]["date"].weekday() == 0  # Monday
    assert records[0]["date"] >= _date.today()


def test_opencities_parser_reads_a_date_window_only_when_asked() -> None:
    html = (
        "<article><h3>Verge Collection</h3>"
        '<div class="next-service">5th Oct - 13th Oct.</div>'
        '<div class="note">Verge Collection 2027</div></article>'
    )

    assert _oc_parse(html) == []
    records = _oc_parse(html, approximate_dates=True)
    # The note names one year, so the window is taken in that year even though
    # it may already have passed.
    assert [r["date"].isoformat() for r in records] == ["2027-10-05"]


def test_opencities_parser_reports_a_property_with_no_service_by_argument() -> None:
    module = _opencities_module()
    raw = module.OpenCitiesResult(
        _OpenCitiesResponse(json_data={"success": False}), "street_address", "1 Main St"
    )

    try:
        module.OpenCitiesParser()(raw)
        raise AssertionError("Expected SourceArgumentNotFound")
    except module.SourceArgumentNotFound as err:
        assert err.argument == "street_address"
        assert "'1 Main St'" in err.message


def test_opencities_parser_flags_a_reply_that_is_not_json() -> None:
    module = _opencities_module()
    raw = module.OpenCitiesResult(
        _OpenCitiesResponse(json_error=True, text="<html>blocked</html>"),
        "address",
        "1 Main St",
    )

    try:
        module.OpenCitiesParser()(raw)
        raise AssertionError("Expected ResponseShapeError")
    except module.response_shape.ResponseShapeError:
        pass


def _oc_projection(note, **projection_args):
    from datetime import date as _date

    module = _opencities_module()
    source = _OpenCitiesSource(lambda url, params: None, predict=True)
    records = [{"type": "General Waste", "date": _date(2027, 2, 1), "note": note}]
    result = module.OpenCitiesProjection(**projection_args)(records, source)
    return [r["date"].isoformat() for r in result]


def test_opencities_projection_projects_a_fortnightly_note_over_four_weeks() -> None:
    assert _oc_projection("Collected fortnightly") == ["2027-02-01", "2027-02-15"]


def test_opencities_projection_projects_a_weekly_note_over_four_weeks() -> None:
    assert _oc_projection("Same day each week") == [
        "2027-02-01",
        "2027-02-08",
        "2027-02-15",
        "2027-02-22",
    ]


def test_opencities_projection_reads_collected_weekly_as_weekly() -> None:
    assert _oc_projection("Collected Weekly. Place bin on verge.") == [
        "2027-02-01",
        "2027-02-08",
        "2027-02-15",
        "2027-02-22",
    ]
    # "bi-weekly" is not a weekly cadence
    assert _oc_projection("Collected bi-weekly") == ["2027-02-01"]


def test_opencities_projection_leaves_a_note_without_a_cadence_alone() -> None:
    assert _oc_projection("Place bin on the kerb") == ["2027-02-01"]
    assert _oc_projection(None) == ["2027-02-01"]


def test_opencities_projection_is_off_unless_its_switch_param_is_set() -> None:
    from datetime import date as _date

    module = _opencities_module()
    records = [
        {"type": "General Waste", "date": _date(2027, 2, 1), "note": "fortnightly"}
    ]
    off = _OpenCitiesSource(lambda url, params: None, predict=False)
    on = _OpenCitiesSource(lambda url, params: None, predict=True)
    projection = module.OpenCitiesProjection(when="predict")

    assert len(list(projection(records, off))) == 1
    assert len(list(projection(records, on))) == 2


def test_wm_com_parses_service_date_delay() -> None:
    module = _get_module("wm_com")

    result = module._parse_holiday_message(
        "Due to the Thanksgiving holiday, your service on 11/24/2026 will be on "
        "a 1 day delay.",
    )

    assert result == {
        module.datetime.datetime(2026, 11, 24): module.datetime.datetime(2026, 11, 25)
    }

    two_digit_year = module._parse_holiday_message(
        "Due to the Thanksgiving holiday, your service on 11/24/26 will be on "
        "a 1 day delay.",
    )

    assert two_digit_year == {
        module.datetime.datetime(2026, 11, 24): module.datetime.datetime(2026, 11, 25)
    }


def test_wm_com_keeps_no_year_holiday_on_today() -> None:
    from datetime import date as _date

    module = _get_module("wm_com")

    result = module._parse_holiday_message(
        "Labor Day is on Monday, September 7th. Weekday collections will "
        "experience a delay of one day.",
        today=_date(2026, 9, 7),
    )

    assert result == {
        module.datetime.datetime(2026, 9, day): module.datetime.datetime(
            2026, 9, day + 1
        )
        for day in range(7, 12)
    }


def test_wm_com_keeps_recent_no_year_holiday_in_current_year() -> None:
    from datetime import date as _date

    module = _get_module("wm_com")

    result = module._parse_holiday_message(
        "Labor Day is on Monday, September 7th. Weekday collections will "
        "experience a delay of one day.",
        today=_date(2026, 9, 8),
    )

    assert result == {
        module.datetime.datetime(2026, 9, day): module.datetime.datetime(
            2026, 9, day + 1
        )
        for day in range(7, 12)
    }


def test_wm_com_rolls_stale_no_year_holiday_into_next_year() -> None:
    from datetime import date as _date

    module = _get_module("wm_com")

    # Once the delayed collection week has fully passed, a year-less notice
    # refers to next year's occurrence rather than the one just gone.
    result = module._parse_holiday_message(
        "Labor Day is on Monday, September 7th. Weekday collections will "
        "experience a delay of one day.",
        today=_date(2026, 9, 20),
    )

    assert result == {
        module.datetime.datetime(2027, 9, day): module.datetime.datetime(
            2027, 9, day + 1
        )
        for day in range(7, 11)
    }


def test_wm_com_parses_weekday_collection_delays() -> None:
    module = _get_module("wm_com")

    labor_day = module._parse_holiday_message(
        "Residential: Labor Day is on Monday, September 7th, 2026, and we will be "
        "closed. Weekday collections will experience a delay of one day. "
        "Commercial: Labor Day is on Monday, September 7th, 2026, and we will be "
        "closed. Weekday collections may experience a delay of up to one day.",
    )
    assert labor_day == {
        module.datetime.datetime(2026, 9, day): module.datetime.datetime(
            2026, 9, day + 1
        )
        for day in range(7, 12)
    }

    thanksgiving = module._parse_holiday_message(
        "Thanksgiving is on Thursday, November 26th, 2026. Weekday collections "
        "will experience a delay of one day.",
    )
    assert thanksgiving == {
        module.datetime.datetime(2026, 11, 26): module.datetime.datetime(2026, 11, 27),
        module.datetime.datetime(2026, 11, 27): module.datetime.datetime(2026, 11, 28),
    }


def test_wm_com_anchors_weekend_holiday_to_observed_weekday() -> None:
    module = _get_module("wm_com")

    # 2026-11-01 is a Sunday, observed on Monday the 2nd: the whole of that
    # week's weekday collections shift.
    sunday = module._parse_holiday_message(
        "The holiday is on Sunday, November 1st, 2026. Weekday collections "
        "will experience a delay of one day.",
    )
    assert sunday == {
        module.datetime.datetime(2026, 11, day): module.datetime.datetime(
            2026, 11, day + 1
        )
        for day in range(2, 7)
    }

    # 2026-11-07 is a Saturday, observed on Friday the 6th: only that Friday
    # is left in the week, so it is the only collection that shifts.
    saturday = module._parse_holiday_message(
        "The holiday is on Saturday, November 7th, 2026. Weekday collections "
        "will experience a delay of one day.",
    )
    assert saturday == {
        module.datetime.datetime(2026, 11, 6): module.datetime.datetime(2026, 11, 7)
    }


def test_wm_com_parses_delay_length_after_the_word_delay() -> None:
    module = _get_module("wm_com")

    numeric_after = module._parse_holiday_message(
        "Due to the holiday, your service on 11/24/2026 will be on a delay of 2 days.",
    )
    assert numeric_after == {
        module.datetime.datetime(2026, 11, 24): module.datetime.datetime(2026, 11, 26)
    }

    spelled_out = module._parse_holiday_message(
        "Due to the holiday, your service on 11/24/2026 will experience a "
        "delay of two days.",
    )
    assert spelled_out == numeric_after

    up_to = module._parse_holiday_message(
        "Due to the holiday, your service on 11/24/2026 may be on a delay of "
        "up to 3 days.",
    )
    assert up_to == {
        module.datetime.datetime(2026, 11, 24): module.datetime.datetime(2026, 11, 27)
    }

    # The original "<n> day delay" ordering must keep working.
    numeric_before = module._parse_holiday_message(
        "Due to the holiday, your service on 11/24/2026 will be on a 2 day delay.",
    )
    assert numeric_before == numeric_after

    # A notice with no delay length at all still yields no adjustment.
    assert (
        module._parse_holiday_message(
            "Due to the holiday, your service on 11/24/2026 may be affected.",
        )
        == {}
    )


# Zone names as Junker publishes them for CIDIU towns, including the shapes that
# are not a plain "street + range": dedicated single-number zones, parity-only
# zones and streets whose name contains "da" or a number.
_CIDIU_ZONES = [
    ("VIA CONDOVE da civico 2 a civico 124 e da civico 1 a civico 123", 1),
    ("CORSO SUSA da 1 a 15", 2),
    ("CORSO SUSA pari da 2 a 314 dispari da 17 a 315", 3),
    ("Viale Antonio Gramsci", 4),
    ("VIA ROMA da civico 1 a civico 99 (tranne civico 51)", 5),
    ("VIA ROMA da civico 51 a civico 51", 6),
    ("Viale Bruno Radich", 7),
    ("Viale Bruno Radich 11", 8),
    ("Via Ettore Montanaro 17", 9),
    ("Via Ettore Montanaro 20", 10),
    ("Via Pietro Micca da civico 1 a civico 32", 11),
    ("Via Pietro Micca 33", 12),
    ("Via Torino civici pari", 13),
    ("Via Torino civici dispari", 14),
    ("VIA LEONARDO DA VINCI", 15),
    ("Piazza 66 Martiri", 16),
]


def _cidiu_zone(street, number):
    module = _get_module("cidiu_it")
    source = module.Source(street=street, street_number=number, city="x")
    return {i: n for n, i in _CIDIU_ZONES}[source._find_zone(_CIDIU_ZONES)]


def test_cidiu_it_matches_zone_by_range_parity_and_exception() -> None:
    assert _cidiu_zone("via condove", 2).startswith("VIA CONDOVE")
    assert _cidiu_zone("CORSO SUSA", 7) == "CORSO SUSA da 1 a 15"
    assert _cidiu_zone("CORSO SUSA", 124).startswith("CORSO SUSA pari")
    assert _cidiu_zone("CORSO SUSA", "17").startswith("CORSO SUSA pari")
    assert _cidiu_zone("VIA ROMA", 50).startswith("VIA ROMA da civico 1")
    assert _cidiu_zone("VIA ROMA", 51) == "VIA ROMA da civico 51 a civico 51"
    # Junker spells the street out where the old calendar abbreviated it.
    assert _cidiu_zone("VIALE GRAMSCI", "18") == "Viale Antonio Gramsci"


def test_cidiu_it_prefers_the_most_specific_zone() -> None:
    assert _cidiu_zone("Viale Bruno Radich", 11) == "Viale Bruno Radich 11"
    assert _cidiu_zone("Viale Bruno Radich", 5) == "Viale Bruno Radich"
    assert _cidiu_zone("Via Ettore Montanaro", 17) == "Via Ettore Montanaro 17"
    assert _cidiu_zone("Via Ettore Montanaro", 20) == "Via Ettore Montanaro 20"
    assert _cidiu_zone("Via Pietro Micca", 33) == "Via Pietro Micca 33"
    assert _cidiu_zone("Via Pietro Micca", 5).startswith("Via Pietro Micca da")


def test_cidiu_it_handles_parity_only_zones_and_street_names_with_da() -> None:
    assert _cidiu_zone("Via Torino", 4) == "Via Torino civici pari"
    assert _cidiu_zone("Via Torino", 5) == "Via Torino civici dispari"
    assert _cidiu_zone("Via Leonardo da Vinci", 3) == "VIA LEONARDO DA VINCI"
    assert _cidiu_zone("Piazza 66 Martiri", 1) == "Piazza 66 Martiri"


def test_cidiu_it_reports_unmatched_addresses() -> None:
    from waste_collection_schedule.exceptions import (
        SourceArgAmbiguousWithSuggestions,
        SourceArgumentNotFoundWithSuggestions,
    )

    module = _get_module("cidiu_it")
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        _cidiu_zone("VIA INESISTENTE", 1)
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        _cidiu_zone("CORSO SUSA", 400)
    with pytest.raises(SourceArgAmbiguousWithSuggestions):
        module.Source(street="VIA VERDI", street_number=7, city="x")._find_zone(
            [("VIA VERDI da 1 a 10", 1), ("VIA VERDI da 5 a 15", 2)]
        )


def test_cidiu_it_fetch_maps_junker_types_to_the_previous_labels() -> None:
    module = _get_module("cidiu_it")
    from waste_collection_schedule import Icons

    calls = []

    def _fetch_junker(self, area=None):
        calls.append(area)
        if area is None:
            return "zones", _CIDIU_ZONES
        return "events", [
            {"date": "2026-01-01", "vbin_desc": "General waste collection"},
            {"date": "2026-01-02", "vbin_desc": "Glass/Cans"},
            {"date": "2026-01-03", "vbin_desc": "Something new"},
        ]

    with patch.object(module.Source, "_fetch_junker", _fetch_junker):
        entries = module.Source(
            street="CORSO SUSA", street_number=124, city="Rivoli"
        ).fetch()

    assert calls == [None, 3]
    assert [e.type for e in entries] == [
        "Indifferenziato",
        "Vetro e lattine",
        "Something new",
    ]
    assert entries[1].icon == Icons.GLASS
