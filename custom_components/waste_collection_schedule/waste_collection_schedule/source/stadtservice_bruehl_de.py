"""StadtService Brühl (stadtservice-bruehl.de).

Demonstrates: a two-POST resolve-then-download shape where the first POST's
only job is to scrape a hidden ``post_district`` field out of the response
HTML, which the second POST then needs alongside the street/house number and
a fixed set of "include every waste type" checkboxes. Both calls are POSTs
(not the GET+GET ``TwoStepRetriever`` supports), hence a source-defined
``retrieve()``.

Labels carry a trailing bin colour (e.g. "Hausmüll (Grau)", "Biotonne
(Braun)"), stripped by ``clean`` before mapping/resolving.
"""

from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_DISTRICT_URL = "https://services.stadtservice-bruehl.de/abfallkalender/"
_CALENDAR_URL = (
    "https://services.stadtservice-bruehl.de/abfallkalender/"
    "individuellen-abfuhrkalender-herunterladen/"
)

_clean_type = label_cleaner(
    strip_suffixes=[" (Grau)", " (Braun)", " (Gelb)", " (Blau)"]
)


@final
class Source(BaseSource):
    TITLE = "StadtService Brühl"
    DESCRIPTION = "Source für Abfallkalender StadtService Brühl"
    URL = "https://stadtservice-bruehl.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        GARDEN_WASTE,
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TEST1": {"strasse": "Badorfer Straße", "hnr": "1"},
    }

    PARAMS = (
        street(field="strasse"),
        house_number(field="hnr"),
    )

    parse = IcsParser(regex=r"(.*?) \- ", split_at=", ")
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Straßenlaub": GARDEN_WASTE},
    )

    def __init__(self, strasse: str, hnr: str):
        super().__init__(strasse=strasse, hnr=hnr)

    def retrieve(self, source):
        session = source.session
        strasse = self.params["strasse"]
        hnr = self.params["hnr"]

        r = session.post(
            _DISTRICT_URL,
            data={
                "street": strasse,
                "street_number": hnr,
                "send_street_and_nummber_data": "",
            },
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        post_district = None
        for tag in soup.find_all("input", type="hidden"):
            if tag.get("name") == "post_district":
                post_district = tag.get("value")

        if not post_district:
            raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, [])

        r = session.post(
            _CALENDAR_URL,
            data={
                "post_year": date.today().year,
                "post_district": post_district,
                "post_street_name": strasse,
                "post_street_number": hnr,
                "checked_waste_type_hausmuell": "on",
                "checked_waste_type_gelber_sack": "on",
                "checked_waste_type_altpapier": "on",
                "checked_waste_type_bio": "on",
                "checked_waste_type_weihnachtsbaeume": "on",
                "checked_waste_type_strassenlaub": "on",
                "form_page_id": "9",
                "reminder_time": "8",
                "send_ics_download_configurator_data": "",
            },
        )
        r.raise_for_status()
        return r
