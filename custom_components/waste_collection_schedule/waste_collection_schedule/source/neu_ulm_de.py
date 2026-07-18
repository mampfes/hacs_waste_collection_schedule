"""Neu-Ulm (neu-ulm.de).

Demonstrates: the "scrape a page for the district's ICS link, then GET it"
shape, a direct fit for ``TwoStepRetriever`` -- ``extract`` finds the matching
anchor and resolves its (possibly relative) href to an absolute URL, which
``schedule_url`` then simply returns unchanged.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import ORGANIC, RECYCLABLES

_HOST_URI = "https://nu.neu-ulm.de"
_CALENDAR_PAGE = (
    f"{_HOST_URI}/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender"
)


def _pick_ics_url(lookup, source) -> str:
    region = source.params["region"]
    soup = BeautifulSoup(lookup.text, "html.parser")
    link = soup.find(lambda tag: tag.name == "a" and region in tag.text)

    if not link or not isinstance(link, Tag):
        raise SourceArgumentNotFound(
            "region",
            region,
            "Check the available Bezirke on "
            "https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender",
        )

    href = link["href"]
    return (
        href
        if isinstance(href, str) and href.startswith("http")
        else f"{_HOST_URI}{href}"
    )


@final
class Source(BaseSource):
    TITLE = "Neu-Ulm"
    DESCRIPTION = "Source for Neu-Ulm."
    URL = "https://nu.neu-ulm.de/buerger-service/leben-in-neu-ulm/abfall-sauberkeit/abfallkalender"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Bezirk 1": {"region": "Bezirk 1"},
        "Bezirk 8": {"region": "Bezirk 8"},
    }

    PARAMS = (district("region", optional=False),)

    RAISE_ON_EMPTY = True

    retrieve = TwoStepRetriever(
        lookup_url=_CALENDAR_PAGE,
        extract=_pick_ics_url,
        schedule_url=lambda key, **_: key,
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Gelber Sack": RECYCLABLES,
            "Grüngut": ORGANIC,
        },
        clean=lambda label: label.replace("Abfuhr ", "").strip(),
    )

    def __init__(self, region: str):
        super().__init__(region=region)
