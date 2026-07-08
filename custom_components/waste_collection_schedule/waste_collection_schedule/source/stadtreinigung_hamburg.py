from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a plain ICS feed (parsers.IcsParser + ICSTransformer) keyed by a
# property id (hnId) carried in the query string. A configured HttpGetRetriever
# supplies the static query params plus the user's hnId; no custom retrieve/parse
# method and no per-source date or icon handling. The German bin names resolve
# through the shared multilingual vocabulary, so there is no type_value_map.
# The legacy asId argument was never used for the fetch and is accepted only for
# back-compat with existing configurations.

API_URL = "https://backend.stadtreinigung.hamburg/kalender/abholtermine.ics"


@final
class Source(BaseSource):
    TITLE = "Stadtreinigung Hamburg"
    DESCRIPTION = "Source for Stadtreinigung Hamburg waste collection."
    URL = "https://www.stadtreinigung.hamburg"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Zabelweg 1B": {"hnId": 53814},
    }

    PARAMS = (text_field("hnId", "House Number ID"), text_field("asId", optional=True))

    # hnId identifies a property; an unknown id yields a feed with no events, so
    # surface that as a bad-argument error rather than a silently-empty calendar.
    RAISE_ON_EMPTY = True

    retrieve = HttpGetRetriever(
        url=API_URL,
        params=lambda hnId, **_: {"hnIds": hnId, "adresse": "MeineAdresse"},
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer()

    def __init__(self, hnId, asId=None):
        super().__init__(hnId=hnId, asId=asId)
