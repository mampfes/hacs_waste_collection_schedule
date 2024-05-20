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

BLACK_LIST = {
    "/doc/source/ics.md",
    "/doc/source/static.md",
    "/doc/source/multiple.md",
    "/doc/source/example.md",
}

START_COUNTRY_SECTION = "<!--Begin of country section-->"
END_COUNTRY_SECTION = "<!--End of country section-->"

START_SERVICE_SECTION = "<!--Begin of service section-->"
END_SERVICE_SECTION = "<!--End of service section-->"


class Section:
    def __init__(self, section):
        self._section = section

    @property
    def start(self):
        return f"<!--Begin of {self._section} section-->"

    @property
    def end(self):
        return f"<!--End of {self._section} section-->"


def split_camel_and_snake_case(s):
    s = re.sub("([a-z0-9])([A-Z])", r"\1 \2", s)  # Split CamelCase
    return s.replace("_", " ").split()  # Split snake_case


def main():
    parser = argparse.ArgumentParser(description="Update docu links.")
    # args = parser.parse_args()

    sources = []

    sources += browse_sources()
    sources += browse_ics_yaml()

    # sort into countries
    country_code_map = make_country_code_map()
    countries = {}

    orphans = []
    for s in sources:
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

    update_json(countries)
    update_readme_md(countries)
    update_info_md(countries)


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

        sig = inspect.signature(module.Source.__init__)
        params = [param.name for param in sig.parameters.values()]

        filename = f"/doc/source/{f}.md"
        if title is not None:
            sources.append(
                SourceInfo(
                    filename=filename,
                    module=f,
                    title=title,
                    url=url,
                    country=country,
                    params=params,
                )
            )

        extra_info = getattr(module, "EXTRA_INFO", [])
        if callable(extra_info):
            extra_info = extra_info()
        for e in extra_info:
            sources.append(
                SourceInfo(
                    filename=filename,
                    module=f,
                    title=e.get("title", title),
                    url=e.get("url", url),
                    country=e.get("country", country),
                    params=params,
                )
            )

    update_awido_de(modules)
    update_ctrace_de(modules)
    update_citiesapps_com(modules)
    update_app_abfallplus_de(modules)
    update_abfallnavi_de(modules)

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
                    module=None,
                    title=data["title"],
                    url=data["url"],
                    country=data.get("country", f.stem.split("_")[-1]),
                    params=[],
                )
            )
            if "extra_info" in data:
                for e in data["extra_info"]:
                    sources.append(
                        SourceInfo(
                            filename=f"/doc/ics/{filename.name}",
                            module=None,
                            title=e.get("title"),
                            url=e.get("url"),
                            country=e.get("country"),
                            params=[],
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
    country_code_map = make_country_code_map()
    countries = {}

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
    url = url.removesuffix("/")
    url = url.removeprefix("http://")
    url = url.removeprefix("https://")
    url = url.removeprefix("www.")
    return url


def update_json(countries):
    params = set()
    # generate country list
    output = {}
    for country in sorted(countries):
        output[country] = []

        for e in sorted(
            countries[country],
            key=lambda e: (e.title.lower(), beautify_url(e.url), e.filename),
        ):
            if e.module is None:
                continue

            output[country].append({"title": e.title, "module": e.module})
            params.update(e.params)

    output["Generic"] = [{"title": "ICS", "module": "ics"}]

    with open(
        "custom_components/waste_collection_schedule/translations/en.json",
        encoding="utf-8",
    ) as f:
        translations = json.load(f)

    arg_translations = translations["config"]["step"]["args"]["data"]
    for param in params:
        if param in arg_translations:
            continue
        arg_translations[param] = " ".join(
            [s.capitalize() for s in split_camel_and_snake_case(param)]
        )

    with open(
        "custom_components/waste_collection_schedule/translations/en.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(translations, f, indent=2)

    with open(
        "custom_components/waste_collection_schedule/sources.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(output))


def update_readme_md(countries):
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


def update_info_md(countries):
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


def update_awido_de(modules):
    module = modules.get("awido_de")
    if not module:
        print("awido_de not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = ""
    for service in sorted(services, key=lambda s: s["service_id"]):
        str += f'- `{service["service_id"]}`: {service["title"]}\n'

    _patch_file("doc/source/awido_de.md", "service", str)


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

    _patch_file("doc/source/c_trace_de.md", "service", str)


def update_citiesapps_com(modules):
    module = modules.get("citiesapps_com")
    if not module:
        print("citiesapps_com not found")
        return
    services = getattr(module, "SERVICE_MAP", [])

    str = "|City|Website|\n|-|-|\n"
    for service in sorted(services, key=lambda service: service["title"]):
        str += f'| {service["title"]} | [{beautify_url(service["url"])}]({service["url"]}) |\n'

    _patch_file("doc/source/citiesapps_com.md", "service", str)


def update_app_abfallplus_de(modules):
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


def update_abfallnavi_de(modules):
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
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)


class SourceInfo:
    def __init__(self, filename, module, title, url, country, params):
        self._filename = filename
        self._module = module
        self._title = title
        self._url = url
        self._country = country
        self._params = params

    def __repr__(self):
        return f"filename:{self._filename}, title:{self._title}, url:{self._url}, country:{self._country}, params:{self._params}"

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
        "code": "it",
        "name": "Italy",
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

if __name__ == "__main__":
    main()
