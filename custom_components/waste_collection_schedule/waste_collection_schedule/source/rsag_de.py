"""RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft (rsag.de).

Demonstrates: a JSON id-lookup cascade (city -> street) feeding a final ICS
download whose path also carries every known waste-type id and a rolling
12-month window. No configured retriever expresses "resolve two ids from two
JSON lookups, then build a months window and download an ICS calendar with
all three baked into the URL", hence a source-defined ``retrieve()``.

The waste-type labels returned (e.g. "Restmülltonne 4-wö.",
"Bio-Container Regelabfuhr für Wohnanlagen") don't match the canonical
vocabulary exactly, so ``clean`` normalises each label to the short generic
term the legacy substring-matching ICON_MAP effectively grouped it under
(Restmüll / Biotonne / Papier / Wertstoff / Weihnachtsbaum) before mapping.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_BASE = "https://www.rsag.de/api"


def _normalise(s: str) -> str:
    """Lowercase and strip for fuzzy matching."""
    return s.strip().lower()


def _clean_type(label: str) -> str:
    """Group a verbose RSAG label under the short term it belongs to.

    Mirrors the legacy substring-matching ICON_MAP: the API returns labels
    like "Restmülltonne 4-wö." or "Bio-Container Regelabfuhr für
    Wohnanlagen" for what is, for icon/type purposes, plain Restmüll/Biotonne.
    """
    lower = label.lower()
    if "restmüll" in lower:
        return "Restmüll"
    if "bio" in lower:
        return "Biotonne"
    if "papier" in lower:
        return "Papier"
    if "wertstoff" in lower:
        return "Wertstoff"
    if "weihnachtsbaum" in lower:
        return "Weihnachtsbaum"
    return label


@final
class Source(BaseSource):
    TITLE = "RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft"
    DESCRIPTION = "Source for RSAG waste collection in the Rhein-Sieg-Kreis, Germany."
    URL = "https://www.rsag.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Königswinter, Winzerstraße": {
            "city": "Königswinter",
            "street": "Winzerstraße",
        },
        "Siegburg, Annostraße": {
            "city": "Siegburg",
            "street": "Annostraße",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.rsag.de/abfallkalender/abfuhrtermine and select "
            "your city and street. Use the exact city and street names shown "
            "in the form."
        ),
        "de": (
            "Besuchen Sie https://www.rsag.de/abfallkalender/abfuhrtermine und "
            "wählen Sie Ihren Ort und Ihre Straße. Verwenden Sie die genauen "
            "Namen wie in der Auswahlliste."
        ),
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
    )

    parse = IcsParser()
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Wertstoff": RECYCLABLES, "Weihnachtsbaum": GARDEN_WASTE},
    )

    def __init__(self, city: str, street: str):
        super().__init__(city=city, street=street)

    def retrieve(self, source):
        session = source.session
        city_value = self.params["city"]
        street_value = self.params["street"]

        # 1. Resolve city -> city_id
        r = session.get(f"{_API_BASE}/city/all")
        r.raise_for_status()
        cities = r.json()

        city_id = None
        city_names = []
        for c in cities:
            city_names.append(c["name"])
            if _normalise(c["name"]) == _normalise(city_value):
                city_id = c["city_id"]
                break
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions("city", city_value, city_names)

        # 2. Resolve street -> street_id
        r = session.get(f"{_API_BASE}/street/filter/{city_id}")
        r.raise_for_status()
        streets = r.json()

        street_id = None
        street_names = []
        for s in streets:
            street_names.append(s["name"])
            if _normalise(s["name"]) == _normalise(street_value):
                street_id = s["street_id"]
                break
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street_value, street_names
            )

        # 3. Fetch all waste type IDs (use all by default)
        r = session.get(f"{_API_BASE}/wastetype/all")
        r.raise_for_status()
        waste_type_ids = ",".join(str(w["wastetype_id"]) for w in r.json())

        # 4. Fetch active months — request a rolling 12-month window
        today = datetime.date.today()
        months = []
        for i in range(12):
            month = today.replace(day=1) + datetime.timedelta(days=32 * i)
            month = month.replace(day=1)
            months.append(month.strftime("%Y-%m"))
        months_param = ",".join(months)

        # 5. Fetch ICS calendar
        ics_url = (
            f"{_API_BASE}/pickup/filter/{street_id}/{waste_type_ids}/{months_param}/ics"
        )
        r = session.get(ics_url)
        r.raise_for_status()
        return r
