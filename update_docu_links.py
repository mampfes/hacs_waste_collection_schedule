#!/usr/bin/env python3

import hashlib
import importlib
import inspect
import json
import re
import site
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Tuple, TypedDict, TypeVar

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

import yaml

from default_translations import default_descriptions, default_translations
from doc_generator import _is_base_source, render_source_doc

SECRET_FILENAME = "secrets.yaml"
SECRET_REGEX = re.compile(r"!secret\s(\w+)")

GENERICS = {
    "/doc/source/ics.md",
    "/doc/source/static.md",
}


BLACK_LIST = {
    *GENERICS,
    "/doc/source/multiple.md",
    "/doc/source/example.md",
}

START_COUNTRY_SECTION = "<!--Begin of country section-->"
END_COUNTRY_SECTION = "<!--End of country section-->"

START_SERVICE_SECTION = "<!--Begin of service section-->"
END_SERVICE_SECTION = "<!--End of service section-->"

LANGUAGES = ["en", "de", "it", "fr", "nl"]
ARG_TRANSLATIONS_TO_KEEP = ["calendar_title"]
ARG_DESCRIPTIONS_TO_KEEP = ["calendar_title"]
ARG_GENERAL_KEYS_TO_KEEP = ["title", "description"]

PACKAGE_DIR = (
    Path(__file__).resolve().parents[0]
    / "custom_components"
    / "waste_collection_schedule"
)
SOURCE_DIR = PACKAGE_DIR / "waste_collection_schedule" / "source"
DOC_SOURCE_DIR = Path(__file__).resolve().parents[0] / "doc" / "source"
DOC_URL_BASE = "https://github.com/mampfes/hacs_waste_collection_schedule/blob/master"

T = TypeVar("T")


def sort_param_dict(d: dict[str, T]) -> dict[str, T]:
    return dict(sorted(d.items()))


def sort_lang_param_dict(d: dict[str, dict[str, T]]) -> dict[str, dict[str, T]]:
    # sort lang
    d = dict(sorted(d.items()))
    # sort param
    for lang in d:
        d[lang] = sort_param_dict(d[lang])
    return d


def extract_urls_from_text(text: str) -> Tuple[str, dict[str, str]]:
    """Extract URLs from text and return cleaned text with placeholder.

    Removes both plain URLs (http://.../https://...) and Markdown links ([text](url)).

    Returns:
        Tuple[str, list[str]]: cleaned text with placeholders, list of extracted URLs
    """
    urls: dict[str, str] = {}
    cleaned_text = text

    def url_to_placeholder(url: str) -> str:
        url = url.split("://", 1)[-1].casefold()
        url = re.sub(r"[^a-z0-9]", "_", url).strip(
            "_"
        )  # replace non alphanumeric characters with underscore
        if len(url) > 100:  # for long urls, we hash to avoid too long placeholders
            url = hashlib.sha1(url.encode()).hexdigest()[:10]
        return f"url_{url}"

    # Extract markdown links [text](url)
    def extract_markdown_link(match: re.Match) -> str:
        url = match.group(2)
        url_placeholder = url_to_placeholder(url)
        urls[url_placeholder] = url
        # Keep the link text but remove the URL part
        return match.group(1) + " (" + url_placeholder + ")"

    for match in re.finditer(r"\[([^\]]+)\]\(([^\)]+)\)", cleaned_text):
        replace = extract_markdown_link(match)
        cleaned_text = cleaned_text.replace(match.group(0), f"{{{replace}}}")

    # Extract plain URLs (http://... or https://...)
    def extract_plain_url(match: re.Match) -> str:
        url = match.group(0)
        url_placeholder = url_to_placeholder(url)
        urls[url_placeholder] = url
        return url_placeholder

    for match in re.finditer(r"https?://[^\s]+", cleaned_text):
        replace = extract_plain_url(match)
        cleaned_text = cleaned_text.replace(match.group(0), f"{{{replace}}}")

    return cleaned_text.strip(), urls


def _normalize_owners(owners) -> list:
    """Normalise a SOURCE_CODEOWNERS / codeowners value into a sorted list of @handles.

    Accepts:
    - None / falsy  -> []
    - str            -> treated as a single handle (not iterated character-by-character)
    - list           -> each element that is a non-empty str is kept; others are
                       silently dropped (guards against accidentally mixed-type lists)

    Every handle is normalised to start with '@'.
    """
    if not owners:
        return []
    if isinstance(owners, str):
        owners = [owners]
    result: list[str] = []
    for entry in owners:
        if not isinstance(entry, str) or not entry.strip():
            continue
        handle = entry.strip()
        if not handle.startswith("@"):
            handle = f"@{handle}"
        result.append(handle)
    return sorted(set(result))


class SourceInfo:
    def __init__(
        self,
        filename: str,
        module: str | None,
        title: str,
        url: str,
        country: str,
        params: list[str],
        extra_info_default_params: dict[str, Any] | None = None,
        custom_param_translation: dict[str, dict[str, str]] | None = None,
        custom_param_description: dict[str, dict[str, str]] | None = None,
        custom_howto: dict[str, str] | None = None,
        source_owners: list[str] | None = None,
    ):
        if custom_howto is None:
            custom_howto = {}
        if custom_param_description is None:
            custom_param_description = {}
        if custom_param_translation is None:
            custom_param_translation = {}
        if extra_info_default_params is None:
            extra_info_default_params = {}
        self._filename = filename
        self._module = module
        self._title = title
        self._url = url
        self._country = country
        self._params = sorted(params)
        self._extra_info_default_params = sort_param_dict(extra_info_default_params)

        url_placeholders: dict[str, str] = {}

        def extract_urls_lang(lang_dict: dict[str, str]) -> dict[str, str]:
            return_val = {}
            for param, translation in lang_dict.items():
                cleaned_translation, urls = extract_urls_from_text(translation)
                return_val[param] = cleaned_translation
                url_placeholders.update(urls)
            return return_val

        def extract_urls(
            lang_dict: dict[str, dict[str, str]],
        ) -> dict[str, dict[str, str]]:
            return {
                param: extract_urls_lang(translations)
                for param, translations in lang_dict.items()
            }

        self._custom_param_translation = default_translations(params)
        self._custom_param_translation.update(custom_param_translation)
        self._custom_param_translation = extract_urls(self._custom_param_translation)

        # sort alphabetically
        self._custom_param_translation = sort_lang_param_dict(
            self._custom_param_translation
        )

        self._custom_param_description = default_descriptions(params)

        # If a parameter has any custom description, do not keep default descriptions
        # for other languages. Mixing default + custom across locales can produce
        # placeholder-set mismatches during Home Assistant translation validation.
        custom_description_params = {
            param
            for lang_descriptions in custom_param_description.values()
            for param in lang_descriptions
        }
        if custom_description_params:
            for lang_descriptions in self._custom_param_description.values():
                for param in custom_description_params:
                    lang_descriptions.pop(param, None)

        self._custom_param_description.update(custom_param_description)
        self._custom_param_description = extract_urls(self._custom_param_description)
        self._url_placeholders = url_placeholders

        self._custom_param_description = sort_lang_param_dict(
            self._custom_param_description
        )

        self._custom_howto = sort_param_dict(custom_howto)
        self._source_owners = _normalize_owners(source_owners)

        for k, v in custom_param_translation.items():
            if k not in LANGUAGES:
                print(
                    f"{self._filename} provided translation for non existing language {k}, You may want to use one of {LANGUAGES} or you need to add the language to LANGUAGES"
                )

            for parameter in v.keys():
                if parameter not in self._params:
                    print(
                        f"{self._filename} provided translation for non existing parameter {parameter}"
                    )

        for k, v in custom_param_description.items():
            if k not in LANGUAGES:
                print(
                    f"{self._filename} provided description for non existing language {k}, You may want to use one of {LANGUAGES} or you need to add the language to LANGUAGES"
                )

            for parameter in v.keys():
                if parameter not in self._params:
                    print(
                        f"{self._filename} provided description for non existing parameter {parameter}"
                    )

    def __repr__(self):
        return f"filename:{self._filename}, title:{self._title}, url:{self._url}, country:{self._country}, params:{self._params}, extra_info_default_params:{self._extra_info_default_params}, custom_param_translation:{self._custom_param_translation}"

    @property
    def filename(self):
        return self._filename

    @property
    def module(self):
        return self._module

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url

    @property
    def country(self):
        return self._country

    @property
    def params(self):
        return self._params

    @property
    def extra_info_default_params(self):
        return self._extra_info_default_params

    @property
    def custom_param_translation(self):
        return self._custom_param_translation

    @property
    def custom_param_description(self):
        return self._custom_param_description

    @property
    def custom_howto(self):
        return self._custom_howto

    @property
    def url_placeholders(self):
        return self._url_placeholders

    @property
    def source_owners(self):
        return self._source_owners


class IcsSourceInfo(SourceInfo):
    def __init__(
        self,
        filename: str,
        title: str,
        url: str,
        country: str,
        limit_params: list[str],
        extra_info_default_params: dict[str, Any] | None = None,
        custom_howto: dict[str, str] | None = None,
        source_owners: list | None = None,
        ics_stem: str | None = None,
    ):
        if custom_howto is None:
            custom_howto = {}
        if extra_info_default_params is None:
            extra_info_default_params = {}
        _, ics_sources = get_source_by_file("ics")
        ics_source = ics_sources[0]
        params = set(ics_source.params) - set(limit_params)
        translations = ics_source.custom_param_translation
        descriptions = ics_source.custom_param_description
        for translation in [*translations.values(), *descriptions.values()]:
            for param in list(translation.keys()):
                if param not in params:
                    translation.pop(param)

        super().__init__(
            filename=filename,
            module=None,
            title=title,
            url=url,
            country=country,
            params=list(params),
            extra_info_default_params=extra_info_default_params,
            custom_param_translation=translations,
            custom_param_description=descriptions,
            custom_howto=custom_howto,
            source_owners=source_owners,
        )
        # ics_stem: the YAML file stem (e.g. "ab_peine_de") used as the key in
        # source_owners.json so that the notify workflow can match what a bug reporter
        # types in the "Source Name" field.
        self._ics_stem = ics_stem

    @property
    def ics_stem(self) -> str | None:
        return self._ics_stem


class Section:
    def __init__(self, section):
        self._section = section

    @property
    def start(self):
        return f"<!--Begin of {self._section} section-->"

    @property
    def end(self):
        return f"<!--End of {self._section} section-->"


class ExtraInfoDict(TypedDict):
    title: NotRequired[str]
    url: NotRequired[str]
    country: NotRequired[str]
    default_params: NotRequired[dict[str, Any]]


class IcsSourceData(TypedDict):
    title: str
    url: str
    description: NotRequired[str]
    howto: dict[str, str]
    country: NotRequired[str]
    default_params: NotRequired[dict[str, Any]]
    test_cases: dict[str, dict[str, Any]]
    extra_info: NotRequired[list[ExtraInfoDict]]
    codeowners: NotRequired[list]


def split_camel_and_snake_case(s: str) -> list[str]:
    s = re.sub("([a-z0-9])([A-Z])", r"\1 \2", s)  # Split CamelCase
    return s.replace("_", " ").split()  # Split snake_case


def update_edpevent_se(modules: dict[str, ModuleType]):
    module = modules.get("edpevent_se")
    if not module:
        print("edpevent_se not found")
        return
    services = getattr(module, "SERVICE_PROVIDERS", {})

    str = ""
    for provider, data in sorted(services.items()):
        str += f"- `{provider}`: {data['title']}\n"

    _patch_file("doc/source/edpevent_se.md", "service", str)


def main() -> None:
    sources: list[SourceInfo] = []

    sources += browse_sources()
    sources += browse_ics_yaml()

    # sort into countries
    country_code_map = make_country_code_map()
    countries: dict[str, list[SourceInfo]] = {}
    generics: list[SourceInfo] = []

    orphans: list[SourceInfo] = []
    for s in sources:
        if s.filename in GENERICS:
            generics.append(s)
        if s.filename in BLACK_LIST:
            continue  # skip

        # extract country code
        code = s.country
        if code in country_code_map:
            countries.setdefault(country_code_map[code]["name"], []).append(s)
        else:
            orphans.append(s)

    if len(orphans) > 0:
        print("Orphaned sources without country =========================")
        for o in orphans:
            print(o)

    update_json(countries, generics=generics)
    update_readme_md(countries)
    update_info_md(countries)


def browse_sources() -> list[SourceInfo]:
    """Browse all .py files in the `source` directory"""
    # add module directory to path
    site.addsitedir(str(PACKAGE_DIR))

    files = filter(
        lambda x: x != "__init__",
        (x.stem for x in SOURCE_DIR.glob("*.py")),
    )

    modules: dict[str, ModuleType] = {}
    sources: list[SourceInfo] = []

    # retrieve all data from sources
    for f in files:
        module, sources_out = get_source_by_file(f)
        modules[f] = module
        sources += sources_out

    update_awido_de(modules)
    update_ctrace_de(modules)
    update_citiesapps_com(modules)
    update_app_abfallplus_de(modules)
    update_abfallnavi_de(modules)
    update_edpevent_se(modules)

    return sources


@lru_cache(maxsize=None)
def get_source_by_file(file: str) -> tuple[ModuleType, list[SourceInfo]]:
    # iterate through all *.py files in waste_collection_schedule/source
    module = importlib.import_module(f"waste_collection_schedule.source.{file}")

    # Read metadata from the Source class first, fall back to module level.
    # New-style (BaseSource) sources keep their metadata on the class; legacy
    # sources expose it at module level. Both are documented the same way so
    # converted sources still appear in the README, sources.json and the
    # generated source_owners.json codeowners mapping.
    source_cls = module.Source

    title = getattr(source_cls, "TITLE", None) or getattr(module, "TITLE", None)
    url = getattr(source_cls, "URL", None) or getattr(module, "URL", None) or ""
    country = (
        getattr(source_cls, "COUNTRY", None)
        or getattr(module, "COUNTRY", None)
        or file.split("_")[-1]
    )

    sig = inspect.signature(source_cls.__init__)
    params = [param.name for param in sig.parameters.values()]
    if "self" in params:
        params.remove("self")
    # New-style (BaseSource) sources carry per-field labels/descriptions on
    # their typed PARAMS instead of PARAM_TRANSLATIONS/PARAM_DESCRIPTIONS dicts.
    # Both have the same {lang: {field: text}} shape, so derive the legacy form
    # from PARAMS here; the rest of the translation generation is unchanged.
    param_translations = (
        getattr(source_cls, "PARAM_TRANSLATIONS", None)
        or getattr(module, "PARAM_TRANSLATIONS", None)
        or _params_labels(source_cls, "labels")
    )
    param_descriptions = (
        getattr(source_cls, "PARAM_DESCRIPTIONS", None)
        or getattr(module, "PARAM_DESCRIPTIONS", None)
        or _params_labels(source_cls, "descriptions")
    )
    howto = (
        getattr(source_cls, "HOWTO", None)
        or getattr(source_cls, "HOW_TO_GET_ARGUMENTS_DESCRIPTION", None)
        or getattr(module, "HOW_TO_GET_ARGUMENTS_DESCRIPTION", {})
    )
    # SOURCE_CODEOWNERS is one name for both styles: pipeline sources declare it
    # on the Source class, legacy sources at module level. Read class first.
    source_owners = getattr(source_cls, "SOURCE_CODEOWNERS", None) or getattr(
        module, "SOURCE_CODEOWNERS", []
    )

    filename = f"/doc/source/{file}.md"

    # New-architecture (BaseSource) sources derive their doc/source/<id>.md from
    # class metadata, so contributors no longer hand-write it. Legacy sources
    # keep their hand-written file untouched.
    if title is not None and _is_base_source(source_cls):
        generate_base_source_doc(file, source_cls)

    sources = []
    if title is not None:
        sources.append(
            SourceInfo(
                filename=filename,
                module=file,
                title=title,
                url=url,
                country=country,
                params=params,
                custom_param_translation=param_translations,
                custom_param_description=param_descriptions,
                custom_howto=howto,
                source_owners=source_owners,
            )
        )

    # A source is one structure covering one or more regions. The typed Region
    # list (REGIONS) is the canonical structure; the deprecated EXTRA_INFO dict
    # list is adapted into Regions at this boundary so the rest of the
    # generation works in Region terms only.
    from waste_collection_schedule.regions import from_extra_info

    region_list = getattr(source_cls, "REGIONS", None)
    if region_list:
        region_list = list(region_list() if callable(region_list) else region_list)
    else:
        legacy = getattr(source_cls, "EXTRA_INFO", None)
        if legacy is None:
            legacy = getattr(module, "EXTRA_INFO", [])
        region_list = from_extra_info(legacy)

    for r in region_list:
        sources.append(
            SourceInfo(
                filename=filename,
                module=file,
                title=r.title or title or "",
                url=r.url or url,
                country=r.country or country,
                params=params,
                custom_param_translation=param_translations,
                custom_param_description=param_descriptions,
                extra_info_default_params=r.params,
                custom_howto=howto,
                source_owners=source_owners,
            )
        )
    return module, sources


def _params_labels(source_cls: Any, attr: str) -> dict[str, dict[str, str]]:
    """Merge per-field ``labels`` or ``descriptions`` across a source's PARAMS.

    Returns the ``{lang: {field: text}}`` mapping the translation generator
    expects (the same shape legacy PARAM_TRANSLATIONS/PARAM_DESCRIPTIONS use),
    so a new-style source's typed PARAMS drive the localised config-flow labels.
    """
    params = getattr(source_cls, "PARAMS", None)
    if not params:
        return {}
    merged: dict[str, dict[str, str]] = {}
    for param in params:
        for lang, mapping in getattr(param, attr, {}).items():
            merged.setdefault(lang, {}).update(mapping)
    return merged


def generate_base_source_doc(file: str, source_cls: Any) -> None:
    """Write doc/source/<file>.md for a new-architecture (BaseSource) source.

    The text is fully derived from the source class metadata via
    render_source_doc(). Legacy (module-level) sources are not handled here;
    they keep their hand-written doc file.
    """
    md = render_source_doc(file, source_cls)
    out_path = DOC_SOURCE_DIR / f"{file}.md"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)


def browse_ics_yaml() -> list[SourceInfo]:
    """Browse all .yaml files which are descriptions for the ICS source"""
    doc_dir = Path(__file__).resolve().parents[0] / "doc"
    yaml_dir = doc_dir / "ics" / "yaml"
    md_dir = doc_dir / "ics"

    files = yaml_dir.glob("*.yaml")
    sources: list[SourceInfo] = []
    for f in files:
        with open(f, encoding="utf-8") as stream:
            # write markdown file
            filename = (md_dir / f.name).with_suffix(".md")
            data: IcsSourceData = yaml.safe_load(stream)

            howto = data.get("howto", {})
            if isinstance(data["howto"], str):
                print(
                    f"howto in {f} is a string, it should be a dictionary with language keys"
                )
                data["howto"] = {"en": howto}

            write_ics_md_file(filename, data)
            howto = data.get("howto", {})
            if isinstance(howto, str):
                print(
                    f"howto in {f} is a string, it should be a dictionary with language keys"
                )
                howto = {"en": howto}

            country = data.get("country", f.stem.split("_")[-1])
            # extract country code
            ics_owners = _normalize_owners(data.get("codeowners", []))
            sources.append(
                IcsSourceInfo(
                    filename=f"/doc/ics/{filename.name}",
                    title=data["title"],
                    url=data["url"],
                    country=country,
                    limit_params=[],
                    extra_info_default_params=data.get("default_params", {}),
                    custom_howto=howto,
                    source_owners=ics_owners,
                    ics_stem=f.stem,
                )
            )
            if "extra_info" in data:
                for e in data["extra_info"]:
                    sources.append(
                        IcsSourceInfo(
                            filename=f"/doc/ics/{filename.name}",
                            title=e.get("title", data["title"]),
                            url=e.get("url", data["url"]),
                            country=e.get("country", country),
                            limit_params=[],
                            extra_info_default_params=data.get("default_params", {}),
                            custom_howto=howto,
                            source_owners=ics_owners,
                            ics_stem=f.stem,
                        )
                    )

    update_ics_md(sources)

    return sources


def write_ics_md_file(filename: Path, data: IcsSourceData) -> None:
    """Write a markdown file for a ICS .yaml file"""
    if "en" not in data["howto"]:
        print(
            f"howto in {filename} does not contain an english translation, please add one"
        )
        return

    md = f"# {data['title']}\n"
    md += "\n"
    md += f"{data['title']} is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.\n"
    md += "\n"
    if "description" in data:
        md += f"{data['description']}\n"
    md += "\n"
    md += "## How to get the configuration arguments\n"
    md += "\n"
    md += f"{data['howto']['en']}"
    md += "\n"
    md += "## Examples\n"
    md += "\n"
    for title, tc in data["test_cases"].items():
        md += f"### {title}\n"
        md += "\n"
        md += "```yaml\n"
        md += "waste_collection_schedule:\n"
        md += "  sources:\n"
        md += "    - name: ics\n"
        md += "      args:\n"
        md += multiline_indent(yaml.dump(tc).rstrip("\n"), 8) + "\n"
        md += "```\n"
        # md += "\n"
    with open(filename, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)


def update_ics_md(sources: list[SourceInfo]):
    country_code_map = make_country_code_map()
    countries: dict = {}

    for s in sources:
        if s.filename in BLACK_LIST:
            continue  # skip

        # extract country code
        code = s.country
        if code in country_code_map:
            countries.setdefault(country_code_map[code]["name"], []).append(s)

    str = ""
    for country in sorted(countries):
        str += f"### {country}\n"
        str += "\n"

        for e in sorted(
            countries[country],
            key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
        ):
            str += f"- [{e.title}]({e.filename}) / {beautify_url(e.url)}\n"

        str += "\n"

    _patch_file("doc/source/ics.md", "service", str)


def multiline_indent(s, numspaces):
    """Indent all lines within the given string by <numspace> spaces"""
    lines = [(numspaces * " ") + line for line in s.split("\n")]
    return "\n".join(lines)


def beautify_url(url):
    if url is None:
        return ""
    url = url.removesuffix("/")
    url = url.removeprefix("http://")
    url = url.removeprefix("https://")
    url = url.removeprefix("www.")
    return url


def update_sources_json(countries: dict[str, list[SourceInfo]]) -> None:
    output: dict[str, list[dict[str, str | dict[str, Any]]]] = {}
    source_metadata_by_module: dict[str, dict[str, Any]] = {}
    source_owners_by_module: dict[str, list[str]] = {}

    for country in ["Generic", *sorted(c for c in countries if c != "Generic")]:
        output[country] = []
        for e in sorted(
            countries[country],
            key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
        ):
            module = e.module if e.module is not None else "ics"
            id = e.filename.split("/")[-1].removesuffix(".md")
            if id != module:
                id = f"{module}_{id}"

            output[country].append(
                {
                    "title": e.title,
                    "module": module,
                    "default_params": e.extra_info_default_params,
                    "id": id,
                }
            )

            # Build metadata for each source (keyed by id for per-source docs)
            if id not in source_metadata_by_module:
                doc_url = DOC_URL_BASE + e.filename
                source_metadata_by_module[id] = {
                    "docs_url": doc_url,
                    "howto": e.custom_howto,
                    "urls": e.url_placeholders,
                }

            # ICS providers are keyed by their YAML file stem (e.g. "ab_peine_de")
            # so the notify workflow can match what a bug reporter types in the
            # "Source Name" field (module == "ics" for all ICS providers).
            if isinstance(e, IcsSourceInfo) and e.ics_stem is not None:
                owner_key = e.ics_stem
            else:
                owner_key = module
            source_owners_by_module.setdefault(owner_key, [])
            source_owners_by_module[owner_key] = sorted(
                set(source_owners_by_module[owner_key]) | set(e.source_owners)
            )

    with open(
        "custom_components/waste_collection_schedule/sources.json",
        "w",
        encoding="utf-8",
        newline="\n",
    ) as f:
        f.write(json.dumps(output, indent=2))

    # Save metadata separately (for runtime use)
    metadata_file = "custom_components/waste_collection_schedule/source_metadata.json"
    with open(metadata_file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(source_metadata_by_module, f, indent=2, ensure_ascii=False)

    source_owner_file = ".github/source_owners.json"
    source_owner_output = {
        "default": [],
        "sources": {
            module: owners
            for module, owners in sorted(source_owners_by_module.items())
            if owners
        },
    }
    with open(source_owner_file, "w", encoding="utf-8") as f:
        json.dump(source_owner_output, f, indent=2, ensure_ascii=False)


def get_custom_translations(
    countries: dict[str, list[SourceInfo]],
) -> Tuple[
    dict[str, dict[str, dict[str, str | None]]],
    dict[str, dict[str, dict[str, str | None]]],
    dict[str, dict[str, str | None]],
    dict[str, str],
]:
    """gets all parameters and its custom translations for all languages

    Args:
        countries (dict[str, list[SourceInfo]]):

    Returns:
        Tuple[dict[str, dict[str, dict[str, str | None]]], dict[str, dict[str, dict[str, str | None]]]]: Param translation dict[MODULE][PARAM][LANG][TRANSLATION|None], Param Description: dict[MODULE][PARAM][LANG][DESCRIPTION|None], Source howto: dict[MODULE][LANG][HOWTO|None], Source doc url: dict[MODULE][URL]
    """
    param_translations: dict[str, dict[str, dict[str, str | None]]] = {}
    param_descriptions: dict[str, dict[str, dict[str, str | None]]] = {}
    source_howto: dict[str, dict[str, str | None]] = {}
    source_doc_url: dict[str, str] = {}

    for country in sorted(countries):
        for e in sorted(
            countries[country],
            key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
        ):
            module = e.module
            if e.module is None:  # ICS source
                module = "ics_" + e.filename.split("/")[-1].removesuffix(".md")

            source_doc_url[module] = DOC_URL_BASE + e.filename

            if module not in param_translations:
                param_translations[module] = {}
            if module not in param_descriptions:
                param_descriptions[module] = {}

            for param in sorted(e.params):
                if param not in param_translations[module]:
                    param_translations[module][param] = {}
                if param not in param_descriptions[module]:
                    param_descriptions[module][param] = {}

            for lang, translations in e.custom_param_translation.items():
                for param, translation in translations.items():
                    param_translations[module][param][lang] = translation

            for lang, descriptions in e.custom_param_description.items():
                for param, description in descriptions.items():
                    param_descriptions[module][param][lang] = description

            source_howto[module] = e.custom_howto

    return param_translations, param_descriptions, source_howto, source_doc_url


def update_json(
    countries: dict[str, list[SourceInfo]], generics: list[SourceInfo] | None = None
):
    if generics is None:
        generics = []
    countries = countries.copy()
    countries["Generic"] = generics
    update_sources_json(countries)
    (
        param_translations,
        param_descriptions,
        source_howto,
        _source_doc_url,
    ) = get_custom_translations(countries)

    for lang in LANGUAGES:
        tranlation_file = (
            f"custom_components/waste_collection_schedule/translations/{lang}.json"
        )
        if not Path(tranlation_file).exists():
            print(f"Translation file {tranlation_file} not found")
            continue

        with open(
            tranlation_file,
            encoding="utf-8",
        ) as f:
            translations = json.load(f)

        translation_for_all = {}
        description_for_all_args = {}
        description_for_all_reconfigure = {}

        keys_for_all_args = {}
        keys_for_all_reconfigure = {}

        for key, value in translations["config"]["step"]["args"]["data"].items():
            if key in ARG_TRANSLATIONS_TO_KEEP:
                translation_for_all[key] = value

        # remove all custom translations and descriptions to automatically remove not needed/unused translations also results in a
        # sorted order of the keys
        step_keys = list(translations["config"]["step"].keys())
        for key in step_keys:
            if key.startswith(("args_", "reconfigure_")):
                translations["config"]["step"].pop(key)

        for key, value in (
            translations["config"]["step"]["args"].get("data_description", {}).items()
        ):
            if key in ARG_DESCRIPTIONS_TO_KEEP:
                description_for_all_args[key] = value
        for key, value in (
            translations["config"]["step"]["reconfigure"]
            .get("data_description", {})
            .items()
        ):
            if key in ARG_DESCRIPTIONS_TO_KEEP:
                description_for_all_reconfigure[key] = value

        for key, value in translations["config"]["step"]["args"].items():
            if key in ARG_GENERAL_KEYS_TO_KEEP:
                keys_for_all_args[key] = value
        for key, value in translations["config"]["step"]["reconfigure"].items():
            if key in ARG_GENERAL_KEYS_TO_KEEP:
                keys_for_all_reconfigure[key] = value

        for module, module_params in param_translations.items():
            translations["config"]["step"][f"args_{module}"] = keys_for_all_args.copy()
            translations["config"]["step"][f"reconfigure_{module}"] = (
                keys_for_all_reconfigure.copy()
            )

            translations["config"]["step"][f"args_{module}"]["data"] = (
                translation_for_all.copy()
            )
            translations["config"]["step"][f"reconfigure_{module}"]["data"] = (
                translation_for_all.copy()
            )

            translations["config"]["step"][f"args_{module}"]["data_description"] = (
                description_for_all_args.copy()
            )
            translations["config"]["step"][f"reconfigure_{module}"][
                "data_description"
            ] = description_for_all_reconfigure.copy()

            for param, languages in module_params.items():
                if languages.get(lang, None) is None:
                    languages[lang] = " ".join(
                        [s.capitalize() for s in split_camel_and_snake_case(param)]
                    )
                translations["config"]["step"][f"args_{module}"]["data"][param] = (
                    languages[lang]
                )
                translations["config"]["step"][f"reconfigure_{module}"]["data"][
                    param
                ] = languages[lang]

            for param, languages in param_descriptions.get(module, {}).items():
                if languages.get(lang, None) is None:
                    continue
                description = languages[lang]
                translations["config"]["step"][f"args_{module}"]["data_description"][
                    param
                ] = description
                translations["config"]["step"][f"reconfigure_{module}"][
                    "data_description"
                ][param] = description

            module_howto = source_howto.get(module, {})

            howto_str = (
                module_howto.get(lang, None) or module_howto.get("en", None) or ""
            )
            howto_str = format_howto(howto_str)
            translations["config"]["step"][f"args_{module}"]["description"] = (
                translations["config"]["step"]["args"]["description"]
            )
            translations["config"]["step"][f"reconfigure_{module}"]["description"] = (
                translations["config"]["step"]["reconfigure"]["description"]
            )

        with open(
            tranlation_file,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)


def format_howto(howto: str) -> str:
    if not howto:
        return ""

    howto = "\n\n" + howto + "\n\n"
    new_howto = ""
    code_opened = False
    code_buffer = ""
    do_not_code = False
    for c in howto:
        match c:
            case "`":
                code_buffer += c if not do_not_code else "'"
                code_opened = not code_opened
                if not code_opened:
                    do_not_code = False
            case "{":
                code_buffer += "&#123;"
                do_not_code = code_opened
            case "}":
                code_buffer += "&#125;"
                do_not_code = code_opened
            case "<":
                code_buffer += "&lt;"
                do_not_code = code_opened
            case ">":
                code_buffer += "&gt;"
                do_not_code = code_opened
            case _:
                code_buffer += c
        if not code_opened:
            new_howto += code_buffer
            code_buffer = ""
        if code_opened and do_not_code:
            code_buffer = code_buffer.replace("`", "'")

    # REGEX replace &lt;https://www.example.com&gt; with https://www.example.com
    new_howto = re.sub(r"&lt;(https?://[^>]+?)&gt;", r"\1", new_howto)
    new_howto = new_howto.replace("``'", "").replace("'``", "")

    return new_howto


def update_readme_md(countries: dict[str, list[SourceInfo]]):
    # generate country list
    str = ""
    for country in sorted(countries):
        str += "<details>\n"
        str += f"<summary>{country}</summary>\n"
        str += "\n"

        for e in sorted(
            countries[country],
            key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
        ):
            # print(f"  {e.title} - {beautify_url(e.url)}")
            str += f"- [{e.title}]({e.filename}) / {beautify_url(e.url)}\n"

        str += "</details>\n"
        str += "\n"

    _patch_file("README.md", "country", str)


def update_info_md(countries: dict[str, list[SourceInfo]]):
    # generate country list
    str = ""
    for country in sorted(countries):
        str += f"| {country} | "
        str += ", ".join(
            [
                e.title
                for e in sorted(
                    countries[country],
                    key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
                )
            ]
        )
        str += " |\n"

    _patch_file("info.md", "country", str)


def update_awido_de(modules: dict[str, ModuleType]):
    module = modules.get("awido_de")
    if not module:
        print("awido_de not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = ""
    for service in sorted(services, key=lambda s: s["service_id"]):
        str += f"- `{service['service_id']}`: {service['title']}\n"

    _patch_file("doc/source/awido_de.md", "service", str)


def update_ctrace_de(modules: dict[str, ModuleType]):
    module = modules.get("c_trace_de")
    if not module:
        print("ctrace_de not found")
        return
    services = getattr(module, "SERVICE_MAP", {})

    str = "|Municipality|service|\n|-|-|\n"
    for service in sorted(
        services.keys(), key=lambda service: services[service]["title"]
    ):
        str += f"| {services[service]['title']} | `{service}` |\n"

    _patch_file("doc/source/c_trace_de.md", "service", str)


def update_citiesapps_com(modules: dict[str, ModuleType]):
    module = modules.get("citiesapps_com")
    if not module:
        print("citiesapps_com not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = "|City|Website|\n|-|-|\n"
    for service in sorted(services, key=lambda service: service["title"]):
        str += f"| {service['title']} | [{beautify_url(service['url'])}]({service['url']}) |\n"

    _patch_file("doc/source/citiesapps_com.md", "service", str)


def update_app_abfallplus_de(modules: dict[str, ModuleType]):
    module = modules.get("app_abfallplus_de")
    if not module:
        print("app_abfallplus_de not found")
        return
    services = getattr(module, "SUPPORTED_SERVICES", {})

    str = "|app_id|supported regions|\n|-|-|\n"
    for app_id, region in services.items():
        regions = ", ".join(region)
        str += f"| {app_id} | {regions} |\n"

    _patch_file("doc/source/app_abfallplus_de.md", "service", str)


def update_abfallnavi_de(modules: dict[str, ModuleType]):
    module = modules.get("abfallnavi_de")
    if not module:
        print("app_abfallplus_de not found")
        return
    services = getattr(module, "SERVICE_DOMAINS", {})

    str = "|Region|service|\n|-|-|\n"
    for region in services:
        str += f"| {region['title']} | {region['service_id']} |\n"

    _patch_file("doc/source/abfallnavi_de.md", "service", str)


def _patch_file(filename, section_id, str):
    # read entire file
    with open(filename, encoding="utf-8") as f:
        md = f.read()

    section = Section(section_id)

    # find beginning and end of country section
    start_pos = md.index(section.start) + len(section.start) + 1
    end_pos = md.index(section.end)

    md = md[:start_pos] + str + md[end_pos:]

    # write entire file
    with open(filename, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)


def make_country_code_map():
    return {x["code"]: x for x in COUNTRYCODES}


COUNTRYCODES = [
    {
        "code": "au",
        "name": "Australia",
    },
    {
        "code": "at",
        "name": "Austria",
    },
    {
        "code": "be",
        "name": "Belgium",
    },
    {
        "code": "ca",
        "name": "Canada",
    },
    {
        "code": "cz",
        "name": "Czech Republic",
    },
    {
        "code": "de",
        "name": "Germany",
    },
    {
        "code": "dk",
        "name": "Denmark",
    },
    {
        "code": "hamburg",
        "name": "Germany",
    },
    {
        "code": "hu",
        "name": "Hungary",
    },
    {
        "code": "ie",
        "name": "Ireland",
    },
    {
        "code": "it",
        "name": "Italy",
    },
    {
        "code": "jp",
        "name": "Japan",
    },
    {
        "code": "lt",
        "name": "Lithuania",
    },
    {
        "code": "lu",
        "name": "Luxembourg",
    },
    {
        "code": "mt",
        "name": "Malta",
    },
    {
        "code": "nl",
        "name": "Netherlands",
    },
    {
        "code": "nz",
        "name": "New Zealand",
    },
    {
        "code": "no",
        "name": "Norway",
    },
    {
        "code": "pl",
        "name": "Poland",
    },
    {
        "code": "pt",
        "name": "Portugal",
    },
    {
        "code": "se",
        "name": "Sweden",
    },
    {
        "code": "sk",
        "name": "Slovakia",
    },
    {
        "code": "si",
        "name": "Slovenia",
    },
    {
        "code": "ch",
        "name": "Switzerland",
    },
    {
        "code": "li",
        "name": "Liechtenstein",
    },
    {
        "code": "us",
        "name": "United States of America",
    },
    {
        "code": "za",
        "name": "South Africa",
    },
    {
        "code": "uk",
        "name": "United Kingdom",
    },
    {
        "code": "fr",
        "name": "France",
    },
    {
        "code": "fi",
        "name": "Finland",
    },
    {
        "code": "pt",
        "name": "Portugal",
    },
]


if __name__ == "__main__":
    main()
