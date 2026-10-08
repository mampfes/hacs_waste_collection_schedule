"""ETRA S.p.A., San Martino di Lupari, Italy.

ETRA publishes its collection calendar as a single PDF whose collection-day
markers are vector-drawn icons with no extractable text layer, linked from a
per-year landing page on the municipality's own website.
``retrievers.PdfLinkRetriever`` finds the current year's PDF; the icon
positions and fill colours are read by the shared
``service.EtraSpa.EtraCalendarParser``, which every ETRA municipality using
this same InDesign template can reuse.
"""

from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.service.EtraSpa import EtraCalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_DOCUMENT_URL = (
    "https://www.comune.sanmartinodilupari.pd.it/"
    "documento_pubblico/calendario-etra-{year}/"
)


@final
class Source(BaseSource):
    TITLE = "ETRA S.p.A."
    DESCRIPTION = "Waste collection schedule for San Martino di Lupari, Italy."
    URL = "https://www.etraspa.it"
    COUNTRY = "it"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@jan-tdy"]
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces (mapped 1:1 in type_value_map
    # below, so nothing falls through to the shared resolver).
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "San Martino di Lupari, zone A": {"zone": "A"},
        "San Martino di Lupari, zone B": {"zone": "B"},
    }

    PARAMS = (dropdown("zone", options=["A", "B"], label="Collection zone"),)

    retrieve = PdfLinkRetriever(
        index_url=lambda **_: _DOCUMENT_URL.format(year=date.today().year),
        pattern=r"\.pdf$",
        select="first",
    )

    parse = EtraCalendarParser(zone_param="zone")

    transform = ICSTransformer(
        type_value_map={
            "Secco residuo": wt.GENERAL_WASTE,
            "Plastica e metalli": wt.RECYCLABLES,
            "Carta e cartone": wt.PAPER,
            "Vetro": wt.GLASS,
            "Verde e ramaglie": wt.GARDEN_WASTE,
            "Umido organico": wt.ORGANIC,
        }
    )
