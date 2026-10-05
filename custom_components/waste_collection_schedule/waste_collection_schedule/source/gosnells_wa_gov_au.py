import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

PAGE_URL = "https://www.gosnells.wa.gov.au/City-Services/Waste-and-Recycling/Find-your-waste-collection-dates"


def _unnumbered(label: str) -> str:
    """Drop a service's trailing number ("Green Waste 1" and "Green Waste 2" are
    the two verge collections of one kind)."""
    return re.sub(r"\s*\d+$", "", label).strip()


@final
class Source(BaseSource):
    TITLE = "City of Gosnells"
    DESCRIPTION = "Source for City of Gosnells, Western Australia."
    URL = "https://www.gosnells.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "15 Mackay Crescent GOSNELLS 6110"},
        "Test_002": {"address": "7 Darkin Drive GOSNELLS 6110"},
        "Test_003": {"address": "35 Prince Street GOSNELLS 6110"},
        "Test_004 (space character test)": {"address": "4A Turley Court LANGFORD 6147"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": f"Use the [City of Gosnells]({PAGE_URL}) website and search for your "
        "collection schedule. Use your address as it is displayed on the search "
        "results page.",
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.gosnells.wa.gov.au",
        headers={
            "user-agent": "Mozilla/5.0",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
            "referer": PAGE_URL,
        },
    )
    # Verge collections are dated as a window ("5th Oct - 13th Oct.") whose
    # year is stated only in the note ("Verge Collection 2026-2027").
    parse = OpenCitiesParser(approximate_dates=True)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        clean=_unnumbered,
        type_value_map={"Bulk Junk": wt.BULKY_WASTE},
    )
