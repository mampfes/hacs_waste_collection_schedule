"""Landkreis Wittmund waste calendar (Sitepark IES platform).

Most Sitepark IES installations resolve a pois from a static, construction-time
``refid`` (or none at all). Wittmund's instead requires a *dynamic*
per-request refid, looked up from the live ``<select id="sf_locid">`` dropdown
on the collection calendar page for the Ort the user entered, then used to
resolve the street to a pois. The shared ``SiteparkIESRetriever`` covers that
with ``refid_page_url``, so this source is a plain composition of shared steps.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.landkreis-wittmund.de"
_API_URL = (
    "https://www.landkreis-wittmund.de/Leben-Wohnen/Wohnen/Abfall/Abfuhrkalender/"
)
_DOWNLOAD_PARAMS = {
    "ArtID[0]": "3105.1",
    "ArtID[1]": "1.4",
    "ArtID[2]": "1.2",
    "ArtID[3]": "1.3",
    "ArtID[4]": "1.1",
    "alarm": "0",
}


@final
class Source(BaseSource):
    TITLE = "Landkreis Wittmund"
    DESCRIPTION = "Source for Landkreis Wittmund waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [
        GARDEN_WASTE,
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "CityWithoutStreet": {"ort": "Werdum"},
        "CityWithStreet": {"ort": "Werdum", "strasse": "alle Straßen"},
    }

    PARAMS = (
        district("ort"),
        street("strasse", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(
        _BASE_URL,
        refid_page_url=_API_URL,
        download_params=_DOWNLOAD_PARAMS,
    )
    parse = parsers.IcsParser()
    # "Baum- und Strauchschnitt", "Biotonne", "Papiertonne" and "Wertstofftonne"
    # already auto-resolve against the shared vocabulary; "Restabfalltonne"
    # doesn't match an alias exactly (the shared aliases use the bare
    # "restabfall" form), so it needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Restabfalltonne": GENERAL_WASTE,
        }
    )

    def __init__(self, ort: str, strasse: str | None = None):
        super().__init__(ort=ort, strasse=strasse)
