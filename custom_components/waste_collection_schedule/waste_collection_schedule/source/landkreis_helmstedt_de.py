"""Landkreis Helmstedt (landkreis-helmstedt.de).

Classic TwoStepRetriever shape: a lookup page lists every municipal ICS
calendar download link; the matching municipality's href is the schedule
URL directly. Each municipal calendar covers every collection area at once,
tagged by a trailing area number ("Restabfall 1", "Altpapier 5", ...); a
custom ``preprocess`` filters to the user's selected area per waste stream
and validates every stream was found, mirroring the legacy source's
per-argument checks.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://www.landkreis-helmstedt.de/portal/seiten/abfuhrkalender-900000002-34150.html"
HEADERS = {"user-agent": "Mozilla"}

COLLECTION_TYPE_RESTABFALL = "Restabfall"
COLLECTION_TYPE_ALTPAPIER = "Altpapier"
COLLECTION_TYPE_GELBER_SACK = "Gelber Sack"
COLLECTION_TYPE_BIOABFALL = "Bioabfall"

# Maps each waste-stream PARAMS field to its collection-type label.
_FIELD_TO_TYPE = {
    "restabfall": COLLECTION_TYPE_RESTABFALL,
    "altpapier": COLLECTION_TYPE_ALTPAPIER,
    "gelber_sack": COLLECTION_TYPE_GELBER_SACK,
    "bioabfall": COLLECTION_TYPE_BIOABFALL,
}


def _pick_calendar_href(lookup, source) -> str:
    soup = BeautifulSoup(lookup.text, "html.parser")
    links = soup.select('.abfrage2 .manager_titel [title="herunterladen/öffnen"]')
    municipal = source.params["municipal"]

    names = []
    for link in links:
        href = link.get("href")
        name = link.get_text()
        if not isinstance(href, str):
            continue
        names.append(name)
        if name.startswith(municipal):
            return href

    raise SourceArgumentNotFoundWithSuggestions("municipal", municipal, names)


@final
class Source(BaseSource):
    TITLE = "Landkreis Helmstedt"
    DESCRIPTION = "Source for Landkreis Helmstedt."
    URL = "landkreis-helmstedt.de"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Grasleben": {
            "municipal": "Grasleben und Velpke",
            "restabfall": 1,
            "bioabfall": 1,
            "gelber_sack": 3,
            "altpapier": 5,
        },
        "Paläon": {
            "municipal": "Schöningen und Heeseberg",
            "restabfall": 1,
            "bioabfall": 1,
            "gelber_sack": 1,
            "altpapier": 2,
        },
        "Rhode": {
            "municipal": "Nord-Elm und Königslutter Ortsteile",
            "restabfall": 2,
            "bioabfall": 2,
            "gelber_sack": 1,
            "altpapier": 2,
        },
        "Essehof": {
            "municipal": "Lehre",
            "restabfall": 1,
            "bioabfall": 1,
            "gelber_sack": 2,
            "altpapier": 1,
        },
        "Braunschweiger Str.": {
            "municipal": "Königslutter Stadtgebiet",
            "restabfall": 1,
            "bioabfall": 1,
            "gelber_sack": 1,
            "altpapier": 1,
        },
        "Barmke": {
            "municipal": "Helmstedt und Ortsteile",
            "restabfall": 3,
            "bioabfall": 3,
            "gelber_sack": 3,
            "altpapier": 5,
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            f"Visit {API_URL} and first get the name of the ICS calendar on the "
            "website for your municipal, then open the related PDF calendar and "
            "find the collection areas."
        ),
    }

    PARAMS = (
        text_field("municipal", label="Municipal"),
        text_field("restabfall", label="Domestic (area number)"),
        text_field("altpapier", label="Paper (area number)"),
        text_field("gelber_sack", label="Recycling (area number)"),
        text_field("bioabfall", label="Organic (area number)"),
    )
    RAISE_ON_EMPTY = True

    retrieve = retrievers.TwoStepRetriever(
        lookup_url=API_URL,
        extract=_pick_calendar_href,
        schedule_url=lambda href, **_: href,
        headers=HEADERS,
    )
    parse = IcsParser()
    transform = ICSTransformer()

    def preprocess(self, records, source=None):
        selection = {
            field_type: str(self.params[field_name])
            for field_name, field_type in _FIELD_TO_TYPE.items()
        }
        seen = dict.fromkeys(selection, False)

        filtered = []
        for date_, summary in records:
            pick_up_type = summary[:-2]
            pick_up_area = summary[-1:]
            if pick_up_type in selection and pick_up_area == selection[pick_up_type]:
                seen[pick_up_type] = True
                filtered.append((date_, pick_up_type))

        # Same validation order as the legacy source.
        for pick_up_type in (
            COLLECTION_TYPE_GELBER_SACK,
            COLLECTION_TYPE_ALTPAPIER,
            COLLECTION_TYPE_BIOABFALL,
            COLLECTION_TYPE_RESTABFALL,
        ):
            if not seen[pick_up_type]:
                field_name = next(
                    name
                    for name, type_ in _FIELD_TO_TYPE.items()
                    if type_ == pick_up_type
                )
                raise SourceArgumentNotFoundWithSuggestions(
                    field_name,
                    self.params[field_name],
                    ["check the PDF calendar for valid collection areas"],
                )

        return filtered

    def __init__(
        self,
        municipal: str,
        restabfall: int,
        altpapier: int,
        gelber_sack: int,
        bioabfall: int,
    ):
        super().__init__(
            municipal=municipal,
            restabfall=restabfall,
            altpapier=altpapier,
            gelber_sack=gelber_sack,
            bioabfall=bioabfall,
        )
