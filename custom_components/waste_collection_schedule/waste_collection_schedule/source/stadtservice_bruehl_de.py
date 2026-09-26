"""StadtService Brühl (stadtservice-bruehl.de).

A two-POST resolve-then-download shape where the first POST's only job is to
scrape a hidden ``post_district`` field out of the response HTML, which the
second POST then needs alongside the street/house number and a fixed set of
"include every waste type" checkboxes. The district lookup is a declared ``Lookup``;
the shared ``LookupChainRetriever`` POSTs for the ICS download.

Labels carry a trailing bin colour (e.g. "Hausmüll (Grau)", "Biotonne
(Braun)"), stripped by ``clean`` before mapping/resolving.
"""

from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner

_DISTRICT_URL = "https://services.stadtservice-bruehl.de/abfallkalender/"
_CALENDAR_URL = (
    "https://services.stadtservice-bruehl.de/abfallkalender/"
    "individuellen-abfuhrkalender-herunterladen/"
)

_clean_type = label_cleaner(
    strip_suffixes=[" (Grau)", " (Braun)", " (Gelb)", " (Blau)"]
)


def _pick_district(response, strasse: str, **_) -> str:
    """Read the collection district back out of the submitted address page."""
    soup = BeautifulSoup(response.text, "html.parser")
    post_district = None
    for tag in soup.find_all("input", type="hidden"):
        if tag.get("name") == "post_district":
            post_district = tag.get("value")

    if not post_district:
        raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, [])
    return str(post_district)


@final
class Source(BaseSource):
    TITLE = "StadtService Brühl"
    DESCRIPTION = "Source für Abfallkalender StadtService Brühl"
    URL = "https://stadtservice-bruehl.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TEST1": {"strasse": "Badorfer Straße", "hnr": "1"},
    }

    PARAMS = (
        street(field="strasse"),
        house_number(field="hnr"),
    )

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _DISTRICT_URL,
                method="POST",
                data=lambda strasse, hnr, **_: {
                    "street": strasse,
                    "street_number": hnr,
                    "send_street_and_nummber_data": "",
                },
                pick=_pick_district,
            ),
        ),
        url=_CALENDAR_URL,
        method="POST",
        data=lambda district, strasse, hnr, **_: {
            "post_year": date.today().year,
            "post_district": district,
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
        raise_for_status=True,
    )
    parse = IcsParser(regex=r"(.*?) \- ", split_at=", ")
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Straßenlaub": wt.GARDEN_WASTE},
    )
