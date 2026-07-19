"""Zweckverband Abfallwirtschaft Werra-Meißner-Kreis.

Demonstrates: the "year-in-URL with a per-year path table" shape, plus a
same-year retry with a differently-cased street name. The provider's URL path
segment is not a simple template — each year (so far) got its own ad-hoc path
when the provider re-platformed — so the mapping is a literal lookup table,
kept verbatim from the legacy source rather than "fixed" or generalised. If
the computed path/street combination comes back empty, the same year is
retried once against the year-agnostic default path with an upper-cased
street name, exactly as the legacy source did.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_YEAR_PATHS = {
    2021: "schnellsuche-2021",
    2023: "schnellsuche-2023",
    2024: "",
    2025: "schnellsuche-2020",
    2026: "persönlicher-terminkalender-2026",
}
_DEFAULT_YEAR_PATH = "persönlicher-terminkalender-2026"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Werra-Meißner-Kreis"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Werra-Meißner-Kreis"
    URL = "https://www.zva-wmk.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    # The ICS transformer resolves the German bin names via the shared vocabulary;
    # these are the canonical types observed from the live provider.
    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        RECYCLABLES,
        ORGANIC,
        PAPER,
        GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Frankenhain": {"city": "Berkatal - Frankenhain", "street": "Teichhof"},
        "Hebenshausen": {
            "city": "Neu-Eichenberg - Hebenshausen",
            "street": "Bachstraße",
        },
        "Vockerode": {"city": "Meißner - Vockerode", "street": "Feuerwehr"},
        "Bad Sooden-Allendorf": {
            "city": "Bad Sooden-Allendorf - Allendorf",
            "street": "Kannhöhe",
        },
    }

    PARAMS = (city(), street())

    def retrieve(self, source):
        today = datetime.date.today()
        years = [today.year, today.year + 1] if today.month == 12 else [today.year]
        return [self._fetch_year(year) for year in years]

    def _fetch_year(self, year: int) -> list[tuple[datetime.date, str]]:
        yearstr = _YEAR_PATHS.get(year, _DEFAULT_YEAR_PATH)
        try:
            return self._fetch_yearstr(yearstr, self.params["street"])
        except Exception:
            return self._fetch_yearstr("", self.params["street"].upper())

    def _fetch_yearstr(
        self, yearstr: str, street: str
    ) -> list[tuple[datetime.date, str]]:
        params = {
            "city": self.params["city"],
            "street": street,
            "type": "all",
            "link": "ical",
        }
        r = self.session.get(f"https://www.zva-wmk.de/termine/{yearstr}", params=params)
        r.raise_for_status()

        dates = ICS(split_at=" / ").convert(r.text)
        if not dates:
            raise ValueError("No entries found")
        return dates

    def parse(self, response, source=None):
        entries: list = []
        for year_entries in response:
            entries.extend(year_entries)
        return entries

    transform = ICSTransformer()

    def __init__(self, city: str, street: str):
        city = city.replace("Hessisch Lichtenau", "HESSISCH+LICHTENAU")
        city = city.replace("Bad Sooden", "BAD+SOODEN")
        city = city.replace("ß", "%C3%9F").upper()
        city = city.replace("Ä", "%C3%84")
        city = city.replace("Ü", "%C3%9C")
        city = city.replace("Ö", "%C3%96")
        city = city.replace(" - ", "_")
        street = street.replace("ß", "%C3%9F").upper()
        street = street.replace("Ä", "%C3%84")
        street = street.replace("Ü", "%C3%9C")
        street = street.replace("Ö", "%C3%96")
        super().__init__(city=city, street=street)
