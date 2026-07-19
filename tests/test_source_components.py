import os
import sys
from collections.abc import Iterable
from functools import cache
from importlib import import_module
from inspect import Parameter, signature
from types import GeneratorType, ModuleType
from typing import Any
from unittest.mock import patch

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
    assert hasattr(module, "TEST_CASES"), f"missing test_cases in source {source}"
    assert isinstance(module.TEST_CASES, dict), (
        f"test_cases must be a dictionary in source {source}"
    )
    assert len(module.TEST_CASES) > 0, (
        f"test_cases must not be empty in source {source}"
    )

    if source not in SOURCES_EXCLUDE_TEST_CASE_CHECK:
        for name, test_case in module.TEST_CASES.items():
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
        init_params_names = set(init_params.keys()) - {"self"}
        mandatory_init_params_names = {
            name
            for name, param in init_params.items()
            if param.default is Parameter.empty
        } - {"self"}
        assert hasattr(module, "TITLE"), f"missing TITLE in source {source}"
        assert hasattr(module, "DESCRIPTION"), f"missing DESCRIPTION in source {source}"
        assert hasattr(module, "URL"), f"missing URL in source {source}"

        _test_source_has_necessary_parameters_test_cases(
            module, source, init_params_names, mandatory_init_params_names
        )

        assert hasattr(module.Source, "fetch"), (
            f"missing fetch method in Source class of source {source}"
        )

        # If the module declares COUNTRY it must be a valid code — update_docu_links.py
        # uses this value directly and silently orphans the source if it doesn't match.
        if hasattr(module, "COUNTRY"):
            assert _is_supported_country_code(module.COUNTRY), (
                f"unsupported country code {module.COUNTRY!r} in source {source}"
            )

        if source not in SOURCES_NO_COUNTRY and not _has_supported_country_code(source):
            assert hasattr(module, "COUNTRY"), (
                f"missing COUNTRY in source {source} or supported countrycode in filename"
            )

        if hasattr(module, "EXTRA_INFO"):
            _test_source_has_necessary_parameters_extra_info(
                module.EXTRA_INFO, source, init_params_names
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

        if hasattr(module, "SOURCE_CODEOWNERS"):
            owners = module.SOURCE_CODEOWNERS
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
    init_params = signature(ICS_MODULE.Source.__init__).parameters
    init_params_names = set(init_params.keys()) - {"self"}
    mandatory_init_params_names = {
        name for name, param in init_params.items() if param.default is Parameter.empty
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


def test_uk_cloud9_client_falls_back_to_secondary_domain(monkeypatch) -> None:
    module = import_module("waste_collection_schedule.service.uk_cloud9_apps")
    requested_urls: list[str] = []

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, dict]:
            return {"wasteCollectionDates": {}}

    class _Session:
        def __init__(self) -> None:
            self.headers: dict[str, str] = {}

        def get(self, url: str, **kwargs) -> _Response:
            requested_urls.append(url)
            if "primary.example.invalid" in url:
                raise module.requests.exceptions.CertificateVerifyError(
                    "SSL host mismatch", 60, None
                )
            return _Response()

    monkeypatch.setattr(module.requests, "Session", lambda **kwargs: _Session())

    client = module.Cloud9Client(
        "rugby",
        api_domains=("https://primary.example.invalid", "https://secondary.example"),
    )
    payload = client._fetch_waste_json("100070200377")

    assert payload == {"wasteCollectionDates": {}}
    assert requested_urls == [
        "https://primary.example.invalid/rugby/citizenmobile/mobileapi/wastecollections/100070200377",
        "https://secondary.example/rugby/citizenmobile/mobileapi/wastecollections/100070200377",
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


def test_uk_cloud9_client_requires_api_domains() -> None:
    module = import_module("waste_collection_schedule.service.uk_cloud9_apps")

    try:
        module.Cloud9Client("rugby", api_domains=())
        raise AssertionError("Expected ValueError when no API domains are configured")
    except ValueError as err:
        assert "At least one API domain" in str(err)


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
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict | None]] = []
        self._responder = responder

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self._responder(url, params)


def _opencities_module():
    return import_module("waste_collection_schedule.service.OpenCities")


def test_opencities_client_resolves_single_address_result() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)

    def responder(url, params):
        assert "/api/v1/myarea/search" in url
        return _OpenCitiesResponse(
            json_data={"Items": [{"Id": "abc-123", "AddressSingleLine": "1 Main St"}]}
        )

    client._session = _OpenCitiesSession(responder)

    assert client.resolve_geolocation_id("1 Main St") == "abc-123"


def test_opencities_client_raises_ambiguous_with_suggestions_on_multiple_matches() -> (
    None
):
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", strict_address_matching=True
    )
    client = module.OpenCitiesClient(config)
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={
                "Items": [
                    {"Id": "a", "AddressSingleLine": "1 Main St, Northtown"},
                    {"Id": "b", "AddressSingleLine": "1 Main St, Southtown"},
                ]
            }
        )
    )

    try:
        client.resolve_geolocation_id("1 Main St")
        raise AssertionError("Expected SourceArgAmbiguousWithSuggestions")
    except module.SourceArgAmbiguousWithSuggestions as err:
        assert list(err.suggestions) == [
            "1 Main St, Northtown",
            "1 Main St, Southtown",
        ]


def test_opencities_client_selects_exact_match_among_multiple_results() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", strict_address_matching=True
    )
    client = module.OpenCitiesClient(config)
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={
                "Items": [
                    {"Id": "a", "AddressSingleLine": "5 Other St, Southtown"},
                    {"Id": "b", "AddressSingleLine": "  1 main st, northtown  "},
                ]
            }
        )
    )

    assert client.resolve_geolocation_id("1 main st, northtown") == "b"


def test_opencities_client_trusts_top_search_result_by_default() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={
                "Items": [
                    {"Id": "a", "AddressSingleLine": "1 Main St, Northtown"},
                    {"Id": "b", "AddressSingleLine": "1 Main St, Southtown"},
                ]
            }
        )
    )

    # With strict_address_matching left at its default (False), the
    # highest-ranked result is used even though it doesn't textually match
    # the query -- avoids turning normal fuzzy-search hits (e.g. missing a
    # state abbreviation) into a hard "ambiguous" failure.
    assert client.resolve_geolocation_id("1 Main St, Somewhere Else") == "a"


def test_opencities_client_raises_not_found_on_empty_search() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(json_data={"Items": []})
    )

    try:
        client.resolve_geolocation_id("nowhere")
        raise AssertionError("Expected SourceArgumentNotFound")
    except module.SourceArgumentNotFound:
        pass


def test_opencities_client_uses_searchfuzzy_and_maxresults_when_configured() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", search_fuzzy=True, max_results=1
    )
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(json_data={"Items": [{"Id": "a"}]})
    )
    client._session = session

    client.resolve_geolocation_id("1 Main St")

    url, params = session.calls[0]
    assert url == "https://example.invalid/api/v1/myarea/searchfuzzy"
    assert params == {"keywords": "1 Main St", "maxresults": 1}


def test_opencities_client_includes_page_link_param_when_configured() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", page_link="/some/page"
    )
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": "<p>no services</p>"}
        )
    )
    client._session = session

    client.fetch_by_geolocation_id("abc")

    _, params = session.calls[0]
    assert params is not None
    assert params["pageLink"] == "/some/page"


def test_opencities_client_get_waste_services_html_returns_raw_fragment() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="note">Collected fortnightly</div>'
        '<div class="next-service">Mon 01/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    assert client.get_waste_services_html("abc") == html


def test_opencities_client_parses_wasteservices_html_into_collections() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
        "<article><h3>Recycling</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert [(e.date.isoformat(), e.type) for e in entries] == [
        ("2027-02-01", "General Waste"),
        ("2027-02-02", "Recycling"),
    ]


def test_opencities_client_does_not_double_count_nested_article_in_result_div() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    html = (
        '<div class="waste-services-result"><article><h3>General Waste</h3>'
        '<div class="next-service">Mon 01/02/2027</div></article></div>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert len(entries) == 1


def test_opencities_client_resolves_icon_via_keywords() -> None:
    from waste_collection_schedule import Icons

    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid",
        icon_keywords={
            "general waste": Icons.GENERAL_WASTE,
            "recycling": Icons.RECYCLING,
        },
    )
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert entries[0].icon == Icons.GENERAL_WASTE


def test_opencities_client_skips_entries_missing_next_service_date() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    html = (
        '<article><h3>General Waste</h3><div class="next-service"></div></article>'
        "<article><h3>Recycling</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert [e.type for e in entries] == ["Recycling"]


def test_opencities_client_filters_by_date_precise_class_when_configured() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", require_date_precise=True
    )
    client = module.OpenCitiesClient(config)
    html = (
        '<div class="waste-services-result date-precise"><h3>General Waste</h3>'
        '<div class="next-service">Mon 01/02/2027</div></div>'
        '<div class="waste-services-result"><h3>Recycling</h3>'
        '<div class="next-service">Every fortnight</div></div>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert [e.type for e in entries] == ["General Waste"]


def test_opencities_client_drops_excluded_types() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", exclude_types=("Burning off",)
    )
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>Burning off</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
        "<article><h3>Rubbish Collection</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert [e.type for e in entries] == ["Rubbish Collection"]


def test_opencities_client_drops_excluded_type_prefixes() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", exclude_type_prefixes=("Calendar",)
    )
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>Calendar - GlassZone 8</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Tue 02/02/2027</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert [e.type for e in entries] == ["General Waste"]


def test_opencities_client_resolves_every_weekday_recurring_text() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Every Monday</div></article>'
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": html}
        )
    )

    entries = client.fetch_by_geolocation_id("abc")

    assert len(entries) == 1
    assert entries[0].date.weekday() == 0  # Monday
    from datetime import date as _date

    assert entries[0].date >= _date.today()


def test_opencities_client_retries_once_on_stale_cached_geolocation_id() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)

    search_calls = {"count": 0}
    html = (
        "<article><h3>General Waste</h3>"
        '<div class="next-service">Mon 01/02/2027</div></article>'
    )

    def responder(url, params):
        if "myarea/search" in url:
            search_calls["count"] += 1
            return _OpenCitiesResponse(json_data={"Items": [{"Id": "fresh-id"}]})
        # wasteservices: fail for the stale cached id, succeed for the fresh one
        if params.get("geolocationid") == "stale-id":
            return _OpenCitiesResponse(json_data={"success": False})
        return _OpenCitiesResponse(json_data={"success": True, "responseContent": html})

    client._session = _OpenCitiesSession(responder)
    client._geolocation_id = "stale-id"

    entries = client.fetch(address="1 Main St")

    assert search_calls["count"] == 1
    assert [e.type for e in entries] == ["General Waste"]
    assert client._geolocation_id == "fresh-id"


def test_opencities_client_bypasses_search_when_geolocation_id_given_directly() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(domain="https://example.invalid")
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": "<p>no services</p>"}
        )
    )
    client._session = session

    client.fetch(geolocation_id="abc")

    assert all("myarea/search" not in url for url, _ in session.calls)


def test_opencities_client_fires_warm_up_url_once_before_wasteservices_when_configured() -> (
    None
):
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid",
        warm_up_url="https://example.invalid/warm",
        warm_up_before="wasteservices",
    )
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": "<p>no services</p>"}
        )
    )
    client._session = session

    client.fetch_by_geolocation_id("abc")
    client.fetch_by_geolocation_id("abc")

    warm_up_calls = [url for url, _ in session.calls if url.endswith("/warm")]
    assert len(warm_up_calls) == 1


def test_opencities_client_fires_warm_up_url_before_search_by_default() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", warm_up_url="https://example.invalid/warm"
    )
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(json_data={"Items": [{"Id": "abc"}]})
    )
    client._session = session

    client.resolve_geolocation_id("1 Main St")

    assert [url for url, _ in session.calls[:1]] == ["https://example.invalid/warm"]


def test_opencities_client_does_not_warm_up_before_wasteservices_by_default() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", warm_up_url="https://example.invalid/warm"
    )
    client = module.OpenCitiesClient(config)
    session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(
            json_data={"success": True, "responseContent": "<p>no services</p>"}
        )
    )
    client._session = session

    client.fetch_by_geolocation_id("abc")

    assert all("/warm" not in url for url, _ in session.calls)


def test_opencities_client_falls_back_from_json_to_xml_search_response() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid", search_response_format="json_then_xml"
    )
    client = module.OpenCitiesClient(config)
    xml = (
        "<Results><PhysicalAddressSearchResult>"
        "<Id>xml-id</Id><AddressSingleLine>1 Main St</AddressSingleLine>"
        "</PhysicalAddressSearchResult></Results>"
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(json_error=True, text=xml)
    )

    assert client.resolve_geolocation_id("1 Main St") == "xml-id"


def test_opencities_client_parses_xml_only_search_response() -> None:
    module = _opencities_module()
    config = module.OpenCitiesConfig(
        domain="https://example.invalid",
        search_response_format="xml",
        strict_address_matching=False,
    )
    client = module.OpenCitiesClient(config)
    xml = (
        "<Results><PhysicalAddressSearchResult>"
        "<Id>xml-id</Id></PhysicalAddressSearchResult></Results>"
    )
    client._session = _OpenCitiesSession(
        lambda url, params: _OpenCitiesResponse(text=xml)
    )

    assert client.resolve_geolocation_id("1 Main St") == "xml-id"


def test_opencities_client_uses_curl_cffi_session_when_configured(monkeypatch) -> None:
    module = _opencities_module()
    created_with = {}

    class _FakeCurlSession:
        def __init__(self, impersonate=None):
            created_with["impersonate"] = impersonate
            self.headers: dict[str, str] = {}

    monkeypatch.setattr(module.curl_cffi_requests, "Session", _FakeCurlSession)

    config = module.OpenCitiesConfig(
        domain="https://example.invalid", use_curl_cffi=True
    )
    client = module.OpenCitiesClient(config)

    assert isinstance(client._session, _FakeCurlSession)
    assert created_with["impersonate"] == "chrome"


def test_mzv_rotenburg_route_filter_without_location() -> None:
    module = _get_module("mzv_rotenburg_bebra_de")

    ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260101
SUMMARY:Entsorgung Gelbe Tonne Route 1
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260102
SUMMARY:Entsorgung Gelbe Tonne Route 2
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260103
SUMMARY:Entsorgung Papier Route West
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260104
SUMMARY:Entsorgung Papier Route Ost
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260105
SUMMARY:Entsorgung Restabfall
END:VEVENT
END:VCALENDAR
"""

    class _Response:
        text = ics_text

        @staticmethod
        def raise_for_status() -> None:
            return None

    with patch.object(module.requests, "get", return_value=_Response()):
        entries = module.Source(
            city="rote", yellow_route="2", paper_route="Ost"
        ).fetch()

    assert [(entry.date.isoformat(), entry.type) for entry in entries] == [
        ("2026-01-02", "Gelbe Tonne"),
        ("2026-01-04", "Papier"),
        ("2026-01-05", "Restabfall"),
    ]
