"""Landkreis Erlangen-Höchstadt.

Demonstrates: the "year-window, single feed per year" shape. The provider's
ICS endpoint takes the year as a query parameter, so a ``retrieve`` override
fetches the current year (and, in December, the following year too, since the
provider publishes it early) and merges the results.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.erlangen-hoechstadt.de/komx/surface/dfxabfallics/GetAbfallIcs"


@final
class Source(BaseSource):
    TITLE = "Landkreis Erlangen-Höchstadt"
    DESCRIPTION = "Source for Landkreis Erlangen-Höchstadt"
    URL = "https://www.erlangen-hoechstadt.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Höchstadt": {"city": "Höchstadt", "street": "Böhmerwaldstraße"},
        "Brand": {"city": "Eckental", "street": "Eckenhaid, Amselweg"},
        "Ortsteile": {"city": "Wachenroth", "street": "Ort inkl. aller Ortsteile"},
    }

    PARAMS = (city(), street())

    def retrieve(self, source):
        today = datetime.date.today()
        years = [today.year, today.year + 1] if today.month == 12 else [today.year]

        texts: list[str] = []
        for year in years:
            payload = {
                "ort": self.params["city"].upper(),
                "strasse": self.params["street"],
                "abfallart": "Alle",
                "jahr": year,
            }
            r = self.session.get(_API_URL, params=payload)
            r.raise_for_status()
            r.encoding = "utf-8"
            texts.append(r.text)
        return texts

    def parse(self, response, source=None):
        entries: list = []
        for text in response:
            entries.extend(ICS(split_at=" / ").convert(text))
        return entries

    transform = ICSTransformer()

    def __init__(self, city: str, street: str):
        super().__init__(city=city, street=street)
