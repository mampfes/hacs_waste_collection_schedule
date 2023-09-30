#!/usr/bin/env python3

import argparse
import importlib
import inspect
import json
import re
import site
from pathlib import Path

import yaml

SECRET_FILENAME = "secrets.yaml"
SECRET_REGEX = re.compile(r"!secret\s(\w+)")

BLACK_LIST = {"/doc/source/ics.md", "/doc/source/static.md", "/doc/source/example.md"}

START_COUNTRY_SECTION = "<!--Begin of country section-->"
END_COUNTRY_SECTION = "<!--End of country section-->"

START_SERVICE_SECTION = "<!--Begin of service section-->"
END_SERVICE_SECTION = "<!--End of service section-->"


class MarkdownSection:
    def __init__(self, section):
        self._section = section

    @property
    def start(self):
        return f"<!--Begin of {self._section} section-->"

    @property
    def end(self):
        return f"<!--End of {self._section} section-->"


class PythonSection:
    def __init__(self, section):
        self._section = section

    @property
    def start(self):
        return f"# Begin of {self._section} section"

    @property
    def end(self):
        return f"# End of {self._section} section"


def main():
    parser = argparse.ArgumentParser(description="Update docu links.")
    # args = parser.parse_args()

    sources = []

    sources += browse_sources()
    sources += browse_ics_yaml()

    # sort into countries
    sources_per_country = {}

    orphans = []
    for s in sources:
        if s.filename in BLACK_LIST:
            continue  # skip

        # extract country code
        code = s.country
        if code in COUNTRY_NAME_MAP:
            sources_per_country.setdefault(code, []).append(s)
        else:
            orphans.append(s)

    if len(orphans) > 0:
        print("Orphaned sources without country =========================")
        for o in orphans:
            print(o)

    update_readme_md(sources_per_country)
    update_info_md(sources_per_country)

    write_config_flow(sources_per_country, sources)


def browse_sources():
    """Browse all .py files in the `source` directory"""
    package_dir = (
        Path(__file__).resolve().parents[0]
        / "custom_components"
        / "waste_collection_schedule"
    )
    source_dir = package_dir / "waste_collection_schedule" / "source"

    # add module directory to path
    site.addsitedir(str(package_dir))

    files = filter(
        lambda x: x != "__init__",
        map(lambda x: x.stem, source_dir.glob("*.py")),
    )

    modules = {}
    sources = []

    # retrieve all data from sources
    for f in files:
        # iterate through all *.py files in waste_collection_schedule/source
        module = importlib.import_module(f"waste_collection_schedule.source.{f}")
        modules[f] = module

        title = module.TITLE
        url = module.URL
        country = getattr(module, "COUNTRY", f.split("_")[-1])

        filename = f"/doc/source/{f}.md"
        if title is not None:
            sources.append(
                SourceInfo(
                    filename=filename,
                    title=title,
                    url=url,
                    country=country,
                    sourcename=f,
                    module=module,
                )
            )

        extra_info = getattr(module, "EXTRA_INFO", [])
        if callable(extra_info):
            extra_info = extra_info()
        for e in extra_info:
            sources.append(
                SourceInfo(
                    filename=filename,
                    title=e.get("title", title),
                    url=e.get("url", url),
                    country=e.get("country", country),
                    sourcename=f,
                )
            )

    update_awido_de(modules)
    update_ctrace_de(modules)
    update_citiesapps_com(modules)

    return sources


def browse_ics_yaml():
    """Browse all .yaml files which are descriptions for the ICS source"""
    doc_dir = Path(__file__).resolve().parents[0] / "doc"
    yaml_dir = doc_dir / "ics" / "yaml"
    md_dir = doc_dir / "ics"

    files = yaml_dir.glob("*.yaml")
    sources = []
    for f in files:
        with open(f, encoding="utf-8") as stream:
            # write markdown file
            filename = (md_dir / f.name).with_suffix(".md")
            data = yaml.safe_load(stream)
            write_ics_md_file(filename, data)

            # extract country code
            sources.append(
                SourceInfo(
                    filename=f"/doc/ics/{filename.name}",
                    title=data["title"],
                    url=data["url"],
                    country=data.get("country", f.stem.split("_")[-1]),
                    sourcename="ics,",
                )
            )
            if "extra_info" in data:
                for e in data["extra_info"]:
                    sources.append(
                        SourceInfo(
                            filename=f"/doc/ics/{filename.name}",
                            title=e.get("title"),
                            url=e.get("url"),
                            country=e.get("country"),
                            sourcename="ics,",
                        )
                    )

    update_ics_md(sources)

    return sources


def write_ics_md_file(filename, data):
    """Write a markdown file for a ICS .yaml file"""
    md = f"# {data['title']}\n"
    md += "\n"
    md += f"{data['title']} is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.\n"
    md += "\n"
    if "description" in data:
        md += f"{data['description']}\n"
    md += "\n"
    md += "## How to get the configuration arguments\n"
    md += "\n"
    md += f"{data['howto']}"
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
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)


def update_ics_md(sources):
    countries = {}

    for s in sources:
        if s.filename in BLACK_LIST:
            continue  # skip

        # extract country code
        code = s.country
        if code in COUNTRY_NAME_MAP:
            countries.setdefault(code, []).append(s)

    str = ""
    for code in sorted(countries, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += f"### {COUNTRY_NAME_MAP[code]}\n"
        str += "\n"

        for e in sorted(
            countries[code], key=lambda e: (e.title.lower(), beautify_url(e.url))
        ):
            str += f"- [{e.title}]({e.filename}) / {beautify_url(e.url)}\n"

        str += "\n"

    _patch_markdown_file("doc/source/ics.md", "service", str)


def multiline_indent(s, numspaces):
    """Indent all lines within the given string by <numspace> spaces"""
    lines = [(numspaces * " ") + line for line in s.split("\n")]
    return "\n".join(lines)


def beautify_url(url):
    url = url.removesuffix("/")
    url = url.removeprefix("http://")
    url = url.removeprefix("https://")
    url = url.removeprefix("www.")
    return url


def update_readme_md(sources_per_country):
    # generate country list
    str = ""
    for code in sorted(sources_per_country, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += "<details>\n"
        str += f"<summary>{COUNTRY_NAME_MAP[code]}</summary>\n"
        str += "\n"

        for e in sorted(
            sources_per_country[code],
            key=lambda e: (e.title.lower(), beautify_url(e.url)),
        ):
            str += f"- [{e.title}]({e.filename}) / {beautify_url(e.url)}\n"

        str += "</details>\n"
        str += "\n"

    _patch_markdown_file("README.md", "country", str)


def update_info_md(sources_per_country):
    # generate country list
    str = ""
    for code in sorted(sources_per_country, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += f"| {COUNTRY_NAME_MAP[code]} | "
        str += ", ".join(
            [
                e.title
                for e in sorted(
                    sources_per_country[code],
                    key=lambda e: (e.title.lower(), beautify_url(e.url)),
                )
            ]
        )
        str += " |\n"

    _patch_markdown_file("info.md", "country", str)


def update_awido_de(modules):
    module = modules.get("awido_de")
    if not module:
        print("awido_de not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = ""
    for service in sorted(services, key=lambda s: s["service_id"]):
        str += f'- `{service["service_id"]}`: {service["title"]}\n'

    _patch_markdown_file("doc/source/awido_de.md", "service", str)


def update_ctrace_de(modules):
    module = modules.get("c_trace_de")
    if not module:
        print("ctrace_de not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = "|Municipality|service|\n|-|-|\n"
    for service in sorted(
        services.keys(), key=lambda service: services[service]["title"]
    ):
        str += f'| {services[service]["title"]} | `{service}` |\n'

    _patch_markdown_file("doc/source/c_trace_de.md", "service", str)


def update_citiesapps_com(modules):
    module = modules.get("citiesapps_com")
    if not module:
        print("citiesapps_com not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = "|City|Website|\n|-|-|\n"
    for service in sorted(services, key=lambda service: service["title"]):
        str += f'| {service["title"]} | [{beautify_url(service["url"])}]({service["url"]}) |\n'

    _patch_markdown_file("doc/source/citiesapps_com.md", "service", str)


def write_config_flow(sources_per_country, sources):
    # generate country list
    str = ""
    for code in sorted(sources_per_country, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += f'    "{code}",\n'

    _patch_python_file(
        "custom_components/waste_collection_schedule/config_flow_const.py",
        "country",
        str,
    )

    # generate sources per country list
    str = ""
    for code in sorted(sources_per_country, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += f"SOURCE_LIST_{code} = [\n"
        sources = [
            source for source in sources_per_country[code] if source.module is not None
        ]
        # sources = [source for source in sources_per_country[code]]
        for e in sorted(sources, key=lambda e: (e.title.lower(), beautify_url(e.url))):
            str += f'    "source_{code}_{e.sourcename}",\n'
        str += f"]\n\n"

    _patch_python_file(
        "custom_components/waste_collection_schedule/config_flow_const.py",
        "source_list",
        str,
    )

    # generate generate data schema for source list per country
    str = ""
    for code in sorted(sources_per_country, key=lambda code: COUNTRY_NAME_MAP[code]):
        str += f'    "{code}": vol.Schema(\n'
        str += "        {\n"
        str += "            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(\n"
        str += "                selector.SelectSelectorConfig(\n"
        str += f"                    options=SOURCE_LIST_{code},\n"
        str += "                    mode=selector.SelectSelectorMode.DROPDOWN,\n"
        str += f'                    translation_key="source_list_{code}",\n'
        str += "                )\n"
        str += "            ),\n"
        str += "        }\n"
        str += "    ),\n"

    _patch_python_file(
        "custom_components/waste_collection_schedule/config_flow_const.py",
        "select_source",
        str,
    )

    # update translations
    tr = load_translations_template()

    selector = tr.setdefault("selector", {})

    country_name_tr = {}
    for code in sources_per_country:
        country_name_tr[code] = COUNTRY_NAME_MAP[code]

        # process sources per country
        source_name_tr = {}
        sources = [
            source for source in sources_per_country[code] if source.module is not None
        ]
        for e in sources:
            source_name_tr[f"source_{code}_{e.sourcename}"] = e.title

        selector[f"source_list_{code}"] = {"options": source_name_tr}

    selector["country"] = {"options": country_name_tr}

    save_translations(tr)


def load_translations_template():
    with open(
        "custom_components/waste_collection_schedule/translations/template/en.json"
    ) as f:
        return json.load(f)


def save_translations(tr):
    with open(
        "custom_components/waste_collection_schedule/translations/en.json", "w"
    ) as f:
        json.dump(tr, f, indent=2)


def inspect_modules(modules):
    for name, module in modules.items():
        sig = inspect.signature(module.Source.__init__)
        print(name)
        # print(module)
        # print(sig.parameters)
        for p in sig.parameters.values():
            if p.default is not p.empty:
                d = f", default: {p.default}"
            else:
                d = ""
            print(f"name:{p.name}{d}")
        print("---")


def _patch_markdown_file(filename, section_id, str):
    # read entire file
    with open(filename, encoding="utf-8") as f:
        md = f.read()

    section = MarkdownSection(section_id)

    # find beginning and end of country section
    start_pos = md.index(section.start) + len(section.start) + 1
    end_pos = md.index(section.end)

    md = md[:start_pos] + str + md[end_pos:]

    # write entire file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)


def _patch_python_file(filename, section_id, str):
    # read entire file
    with open(filename, encoding="utf-8") as f:
        md = f.read()

    section = PythonSection(section_id)

    # find beginning and end of country section
    start_pos = md.index(section.start) + len(section.start) + 1
    end_pos = md.index(section.end)

    md = md[:start_pos] + str + md[end_pos:]

    # write entire file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)


class SourceInfo:
    def __init__(self, filename, title, url, country, sourcename, module=None):
        self._filename = filename  # markdown documentation file name including path
        self._title = title  # source title
        self._url = url  # source url
        self._country = country  # related country code
        self._sourcename = sourcename  # source file name (excluding .py)
        self._module = module  # loaded Python module for source

    def __repr__(self):
        return f"filename:{self._filename}, title:{self._title}, url:{self._url}, country:{self._country}"

    @property
    def filename(self):
        return self._filename

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
    def sourcename(self):
        return self._sourcename

    @property
    def module(self):
        return self._module


def make_country_name_map():
    return {x["code"]: x["name"] for x in COUNTRYCODES}


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
        "code": "lt",
        "name": "Lithuania",
    },
    {
        "code": "lu",
        "name": "Luxembourg",
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
        "code": "se",
        "name": "Sweden",
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
        "code": "us",
        "name": "United States of America",
    },
    {
        "code": "uk",
        "name": "United Kingdom",
    },
    {
        "code": "fr",
        "name": "France",
    },
]

COUNTRY_NAME_MAP = make_country_name_map()

if __name__ == "__main__":
    main()
