"""London Borough of Bexley (bexley.gov.uk).

Demonstrates: the UK htmx polling shape. The property page kicks off
server-side calendar generation; the site's own page polls the ``.ics``
endpoint every 2 seconds (``hx-trigger="every 2s"``) until it's ready.
``PollingIcsRetriever`` mirrors that polling; ``IcsParser`` + ``ICSTransformer``
do the rest. The only source-specific code is the URL template, the
waste-type map, and a small label cleaner: the raw summary is
"<Bin Name> Bin (<detail>)" and only the bin-name prefix identifies the type.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import PollingIcsRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)


def _clean_bin_label(label: str) -> str:
    """Strip the " Bin" suffix and any trailing "(...)" detail.

    The raw ICS summary is e.g. "Green Wheelie Bin (General Waste)"; only the
    "Green Wheelie" prefix identifies which bin it is.
    """
    return label.replace(" Bin", "").split("(")[0].strip()


@final
class Source(BaseSource):
    TITLE = "London Borough of Bexley"
    DESCRIPTION = "Source for bexley.gov.uk services for London Borough of Bexley, UK."
    URL = "https://bexley.gov.uk"
    COUNTRY = "uk"

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "200001604426"},
        "Test_002": {"uprn": 100020194783},
        "Test_003": {"uprn": "100020195768"},
        "Test_004": {"uprn": 100020200324},
    }

    PARAMS = (uprn(),)

    retrieve = PollingIcsRetriever(
        url=lambda uprn, **_: f"https://waste.bexley.gov.uk/waste/{uprn}"
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Green Wheelie": GENERAL_WASTE,
            "Brown Caddy": FOOD_WASTE,
            "Brown Wheelie": ORGANIC,
            "Blue Lidded Wheelie": PAPER,
            "White Lidded Wheelie": GLASS,
            "Recycling Box": RECYCLABLES,
        },
        clean=_clean_bin_label,
    )

    def __init__(self, uprn: str):
        super().__init__(uprn=uprn)
