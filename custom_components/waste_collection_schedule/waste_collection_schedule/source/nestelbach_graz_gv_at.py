"""Nestelbach bei Graz (nestelbach-graz.gv.at).

Same municipal WordPress site template as ``kumberg_gv_at``: the calendar page
lists one ``?ical=download`` subscription link per waste type (``a.cal-abbo``
with ``/abfalltyp/<type>/`` in the href), and every feed is fetched and merged
by ``service.ICS.IcsIndexRetriever``. Each feed only carries the next one to
three collections, so the schedule is short but always current. Feeds for types
without an upcoming date (Altglas, Altmetall, Sperrmüll) are simply empty.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://www.nestelbach-graz.gv.at/kalender/"


@final
class Source(BaseSource):
    TITLE = "Nestelbach bei Graz"
    DESCRIPTION = "Source for Nestelbach bei Graz."
    URL = "https://www.nestelbach-graz.gv.at"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {"Whole Nestelbach": {}}

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = IcsIndexRetriever(
        index_url=API_URL,
        link_selector="a.cal-abbo",
        pattern=r"/abfalltyp/",
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    # Restmüll, Biomüll, Altpapier, Altglas and Sperrmüll resolve through the
    # shared vocabulary; only the two local labels need mapping.
    transform = ICSTransformer(
        type_value_map={
            "Leichtfraktion": wt.RECYCLABLES,
            "Altmetall": wt.METAL,
        },
    )
