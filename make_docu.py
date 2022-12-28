#!/usr/bin/env python3

import argparse
import importlib
import re
import site
from pathlib import Path

import yaml

SECRET_FILENAME = "secrets.yaml"
SECRET_REGEX = re.compile(r"!secret\s(\w+)")

BLACK_LIST = {"ics", "static", "example"}


def main():
    parser = argparse.ArgumentParser(description="Test sources.")
    args = parser.parse_args()

    # read secrets.yaml
    secrets = {}
    try:
        with open(SECRET_FILENAME) as stream:
            try:
                secrets = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    except FileNotFoundError:
        # ignore missing secrets.yaml
        pass

    package_dir = (
        Path(__file__).resolve().parents[0]
        / "custom_components"
        / "waste_collection_schedule"
    )
    source_dir = package_dir / "waste_collection_schedule" / "source"
    print(source_dir)

    # add module directory to path
    site.addsitedir(str(package_dir))

    files = filter(
        lambda x: x != "__init__",
        map(lambda x: x.stem, source_dir.glob("*.py")),
    )

    sources = []

    # retrieve all data from sources
    for f in files:
        # iterate through all *.py files in waste_collection_schedule/source
        module = importlib.import_module(f"waste_collection_schedule.source.{f}")

        title = module.TITLE
        url = module.URL
        country = getattr(module, "COUNTRY", f.split("_")[-1])

        if title is not None:
            sources.append(
                SourceInfo(filename=f, title=title, url=url, country=country)
            )

        extra_info = getattr(module, "EXTRA_INFO", [])
        if callable(extra_info):
            extra_info = extra_info()
        for e in extra_info:
            sources.append(
                SourceInfo(
                    filename=f,
                    title=e.get("title", title),
                    url=e.get("url", url),
                    country=e.get("country", country),
                )
            )

    # sort into countries
    country_code_map = make_country_code_map()
    countries = {}
    zombies = []
    for s in sources:
        if s.filename in BLACK_LIST:
            continue  # skip

        # extract country code
        code = s.country
        if code in country_code_map:
            countries.setdefault(country_code_map[code]["name"], []).append(s)
        else:
            zombies.append(s)

    for country in sorted(countries):
        print(f"{country}")
        for e in sorted(countries[country], key=lambda e: e.title.lower()):
            print(f"  {e.title} - {beautify_url(e.url)}")

    print("Zombies =========================")
    for z in zombies:
        print(z)


def beautify_url(url):
    url = url.removesuffix("/")
    url = url.removeprefix("https://")
    url = url.removeprefix("www.")
    return url


class SourceInfo:
    def __init__(self, filename, title, url, country):
        self._filename = filename
        self._title = title
        self._url = url
        self._country = country

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
        "code": "de",
        "name": "Germany",
    },
    {
        "code": "hamburg",
        "name": "Germany",
    },
    {
        "code": "lt",
        "name": "Lithuania",
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
]

if __name__ == "__main__":
    main()
