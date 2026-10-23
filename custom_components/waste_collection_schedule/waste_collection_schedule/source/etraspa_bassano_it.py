"""ETRA S.p.A., Bassano del Grappa, Italy.

ETRA publishes one calendar PDF per collection zone for Bassano del Grappa on
its own website, under a predictable file name that carries the year and the
zone letter. The collection-day markers are vector-drawn icons with no text
layer; ``service.EtraSpa.EtraCalendarParser`` reads their positions and fill
colours, here in its single-zone layout (no "ZONA A / ZONA B" sub-columns).
"""

from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.EtraSpa import EtraCalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_PDF_URL = (
    "https://www.etraspa.it/sites/etraspa.it/files/"
    "Bassano_CalendA4_2Z_{year}_{zone}.pdf"
)


@final
class Source(BaseSource):
    TITLE = "ETRA S.p.A. - Bassano del Grappa"
    DESCRIPTION = "Waste collection schedule for Bassano del Grappa, Italy."
    URL = "https://www.etraspa.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Bassano del Grappa, zone C": {"zone": "C"},
        "Bassano del Grappa, zone D": {"zone": "D"},
    }

    PARAMS = (dropdown("zone", options=["C", "D"], label="Collection zone"),)

    retrieve = HttpGetRetriever(
        url=lambda zone, **_: _PDF_URL.format(
            year=date.today().year, zone=str(zone).strip().upper()
        )
    )

    parse = EtraCalendarParser(zone_param=None)

    transform = ICSTransformer(
        type_value_map={
            "Secco residuo": wt.GENERAL_WASTE,
            "Plastica e metalli": wt.RECYCLABLES,
            "Carta e cartone": wt.PAPER,
            "Vetro": wt.GLASS,
            "Umido organico": wt.ORGANIC,
        }
    )
