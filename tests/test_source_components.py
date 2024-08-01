import os
import sys
from functools import cache
from importlib import import_module
from inspect import Parameter, signature
from types import GeneratorType, ModuleType
from typing import Any, Iterable, Type

import yaml

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..")
)  # isort:skip # noqa: E402
from update_docu_links import BLACK_LIST, COUNTRYCODES  # isort:skip # noqa: E402

SOURCES_NO_COUNTRY = [g.split("/")[-1].removesuffix(".md") for g in BLACK_LIST]
SOURCES_TO_EXCLUDE = ["__init__.py", "example.py"]
SOURCES_EXCLUDE_TEST_CASE_CHECK = ["multiple"]


EXTRA_INFO_TYPES: dict[str, Type] = {
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
    with open(os.path.join(ICS_YAML_PATH, f"{source}.yaml")) as file:
        return yaml.safe_load(file)


def _is_supported_country_code(code: str) -> bool:
    return any(code == country["code"] for country in COUNTRYCODES)


def _has_supported_country_code(file: str) -> bool:
    if file.endswith(".py"):
        file.removesuffix(".py")
    code = file.split("_")[-1]
    return _is_supported_country_code(code)


def test_source_md_exists() -> None:
    sources = _get_sources()
    source_md = _get_source_md()
    for source in sources:
        assert source in source_md, f"missing source markdown file: {source}.md"


def test_no_extra_source_mds() -> None:
    sources = _get_sources()
    source_md = _get_source_md()
    for source in source_md:
        assert source in sources, f"found orphaned source markdown file: {source}.md"


def test_ics_md_exists() -> None:
    sources = _get_ics_sources()
    source_md = _get_ics_md()
    for source in sources:
        assert source in source_md, f"missing ics markdown file: {source}.md"


def test_no_extra_ics_mds() -> None:
    sources = _get_ics_sources()
    source_md = _get_ics_md()
    for source in source_md:
        assert source in sources, f"found orphaned ics markdown file: {source}.md"


def _test_case_check(
    name: Any,
    test_case: Any,
    source: str,
    init_params_names: Iterable[str],
    mandatory_init_params_names: Iterable[str],
) -> None:
    assert isinstance(name, str), f"test_case key must be a string in source {source}"
    assert isinstance(
        test_case, dict
    ), f"test_case value must be a dictionary in source {source}"
    for test_case_param in test_case.keys():
        assert isinstance(
            test_case_param, str
        ), f"test_case keys must be strings in source {source}"
        assert (
            test_case_param in init_params_names
        ), f"test_case key {test_case_param} not a valid parameter in Source class in source {source}"

    for param in mandatory_init_params_names:
        assert (
            param in test_case.keys()
        ), f"missing mandatory parameter ({param}) in test_case '{name}' in source {source}"


def _test_source_has_necessary_parameters_test_cases(
    module: ModuleType,
    source: str,
    init_params_names: Iterable[str],
    mandatory_init_params_names: Iterable[str],
) -> None:
    assert hasattr(module, "TEST_CASES"), f"missing test_cases in source {source}"
    assert isinstance(
        module.TEST_CASES, dict
    ), f"test_cases must be a dictionary in source {source}"
    assert (
        len(module.TEST_CASES) > 0
    ), f"test_cases must not be empty in source {source}"

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
            assert False, f"EXTRA_INFO() function in source {source} failed with {e}"

        # check if is iterable (list, tupüle, set)
        assert isinstance(
            extra_info, (list, tuple, set, GeneratorType)
        ), f"EXTRA_INFO in source {source}, must be or return an iterable"
        # check if all items are dictionaries
        for item in extra_info:
            assert isinstance(
                item, dict
            ), f"EXTRA_INFO in source {source}, must return a list of dictionaries, but at least one is not a dict"
            assert (
                "title" in item
            ), f"EXTRA_INFO in source {source}, must have a new title key in each dictionary"
            assert isinstance(
                item["title"], str
            ), f"EXTRA_INFO in source {source}, must have a string title key in each dictionary"

            for key in item.keys():
                assert isinstance(
                    key, str
                ), f"EXTRA_INFO in source {source}, must only have string keys in each dictionary"
                assert (
                    key in EXTRA_INFO_KEYS
                ), f"Found unknown key {key} in source {source}, must have only the following keys: {EXTRA_INFO_KEYS}"
                assert isinstance(
                    item[key], EXTRA_INFO_TYPES[key]
                ), f"EXTRA_INFO in source {source}, key {key} must have type {EXTRA_INFO_TYPES[key]}"

            if "country" in item:
                assert _is_supported_country_code(
                    item["country"]
                ), f"unsupported country code in source {source} in EXTRA_INFO"
            if "default_params" in item:
                for key in item["default_params"].keys():
                    assert isinstance(
                        key, str
                    ), f"EXTRA_INFO in source {source}, default_params keys must be strings"
                    assert (
                        key in init_params_names
                    ), f"EXTRA_INFO in source {source}, default_params key {key} not a valid parameter in Source class"


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

        assert hasattr(
            module.Source, "fetch"
        ), f"missing fetch method in Source class of source {source}"

        if source not in SOURCES_NO_COUNTRY and not _has_supported_country_code(source):
            assert hasattr(
                module, "COUNTRY"
            ), f"missing COUNTRY in source {source} or supported countrycode in filename"
            assert _is_supported_country_code(
                module.COUNTRY
            ), f"unsupported country code in source {source}"

        if hasattr(module, "EXTRA_INFO"):
            _test_source_has_necessary_parameters_extra_info(
                module.EXTRA_INFO, source, init_params_names
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
        assert "test_cases" in data, f"missing test_cases in yaml file {source}.yaml"
        assert isinstance(
            data["test_cases"], dict
        ), f"test_cases must be a dictionary in yaml file {source}.yaml"
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
