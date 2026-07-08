import urllib.parse
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a plain ICS feed (parsers.IcsParser + ICSTransformer) whose
# address sits in the URL *path*, not the query string. A configured
# HttpGetRetriever with a callable url builds the path from the user's city/area;
# no custom retrieve/parse method and no per-source date or icon handling. The
# German bin names resolve through the shared multilingual vocabulary, so there
# is no type_value_map.

_QUERY = "RESTMUELL=true&RESTMUELL_SINGLE=true&BIO=true&YELLOW_SACK=true&PAPER=true"


def _ics_url(city: str, area: str, **_: object) -> str:
    place = urllib.parse.quote(f"{city} - {area}")
    return f"https://www.abfalltermine-forchheim.de/Forchheim/Landkreis/{place}/ics?{_QUERY}"


@final
class Source(BaseSource):
    TITLE = "Abfalltermine Forchheim"
    DESCRIPTION = "Source for Landkreis Forchheim."
    URL = "https://www.abfalltermine-forchheim.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Dormitz": {"city": "Dormitz", "area": "Dormitz"},
        "Rüsselbach": {"city": "Igensdorf", "area": "Oberrüsselbach"},
        "Kellerstraße": {
            "city": "Forchheim",
            "area": "Untere Kellerstraße (ab Adenauerallee bis Piastenbrücke)",
        },
    }

    PARAMS = (text_field("city", "City"), text_field("area", "Area"))

    retrieve = HttpGetRetriever(url=_ics_url)
    # min_events=1: a valid place returns a feed with events; an unknown
    # city/area yields a non-ICS error page (no events), logged and raised as
    # ResponseShapeError rather than silently returning nothing.
    parse = parsers.IcsParser(min_events=1)
    transform = ICSTransformer()

    def __init__(self, city: str, area: str):
        super().__init__(city=city, area=area)
