"""RESO GmbH (reso-gmbh.de).

Composes: the ICS platform's
:class:`~waste_collection_schedule.service.ICS.IcsSessionRetriever`. The
provider answers a single form POST with the calendar itself rather than
redirecting to a download URL, which is what ``feed_url=None`` (the feed is the
last step's own response) describes. The form takes the calendar year, so the
whole one-step chain is what runs per year: near year-end the provider's own
calendar app also shows the first weeks of the following year, and
``lookahead_month=12`` mirrors that, best-effort, so a year that is not
published yet leaves the current one intact.

Parsing is the plain ``IcsParser`` with the same ``split_at`` the legacy
``ICS()`` call used.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ICS import IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://reso-gmbh.abfallkalender.services/php/Kalender-2-ICS.php"

_TOWNS = (
    "Bad-König",
    "Brensbach",
    "Breuberg",
    "Brombachtal",
    "Erbach",
    "Fränkisch-Crumbach",
    "Höchst",
    "Lützelbach",
    "Michelstadt",
    "Mossautal",
    "Oberzent",
    "Reichelsheim",
)


@final
class Source(BaseSource):
    TITLE = "RESO"
    DESCRIPTION = "Source for RESO."
    URL = "https://reso-gmbh.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Reichelsheim Kerngemeinde": {
            "ort": "Reichelsheim",
            "ortsteil": "Kerngemeinde",
        },
    }

    REGIONS = tuple(region(town, ort=town) for town in _TOWNS)

    PARAMS = (
        municipality(field="ort"),
        district(field="ortsteil"),
    )

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": _API_URL,
                "method": "POST",
                "data": lambda ort, ortsteil, year, **_: {
                    "Ort": ort,
                    "Ortsteil": ortsteil,
                    "Jahr": year,
                    "art": 1,
                    "downOderurl2": "Semikolon",
                },
            }
        ],
    )
    parse = parsers.EachResponse(parsers.IcsParser(split_at=r" \+ "))

    transform = ICSTransformer(
        type_value_map={
            "restmüll": GENERAL_WASTE,
            "biotonne": ORGANIC,
            "papiertonne": PAPER,
            "gelber-sack": RECYCLABLES,
        }
    )
