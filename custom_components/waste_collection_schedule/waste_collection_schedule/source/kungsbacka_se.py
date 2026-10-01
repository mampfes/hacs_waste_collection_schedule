import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_BASE_URL = "https://sjalvservice.kungsbacka.se"

# "Kommande hämtningar av hushållsavfall:" -> "hushållsavfall"
_HEADER = re.compile(r"Kommande h.+?mtningar av (.+?):?\s*$")


def _address_hit(response, *, street_address: str, **_) -> list:
    """The first address the search returns, as ``[uuid, full address, x, y, property identity, ...]``."""
    results = response.json()
    if not results:
        raise SourceArgumentNotFound("street_address", street_address)
    return results[0]


def _type(td: Tag) -> str:
    header = td.find_parent("table").find("th").get_text().strip()
    match = _HEADER.match(header)
    return match.group(1) if match else header.rstrip(":")


@final
class Source(BaseSource):
    TITLE = "Kungsbacka kommun"
    DESCRIPTION = "Source for Kungsbacka kommun waste collection, Sweden."
    URL = "https://sjalvservice.kungsbacka.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Storgatan 1 Kungsbacka": {"street_address": "Storgatan 1 Kungsbacka"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and house number as shown on the "
            "[Kungsbacka self-service portal]"
            "(https://sjalvservice.kungsbacka.se/oversikt/flow/4587), e.g. "
            "`Lundaväg 14` or `Lundaväg 14 Särö`. Swedish characters (ä, å, ö) "
            "are supported."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_BASE_URL}/lmsearch/addresses",
                params=lambda street_address, **_: {"q": street_address},
                pick=_address_hit,
            ),
        ),
        url=f"{_BASE_URL}/oversikt/flow/4587",
        method="POST",
        data=lambda hit, **_: {
            "submitmode": "true",
            "q182296_searchservice": "ADDRESS",
            "q182296_propertyUnitDesignation": "",
            "q182296_address": hit[1],
            "q182296_propertyObjectIdentity": hit[4],
            "q182296_addressUUID": hit[0],
        },
    )
    parse = parsers.HtmlParser("div#query_182297 article table td")
    transform = HtmlTransformer(
        # "2026-06-03 - onsdag vecka 23"
        date_getter=lambda td: td.get_text().strip().split(" - ")[0],
        type_getter=_type,
        skip_unparseable_dates=True,
        type_value_map={
            "hushållsavfall": wt.GENERAL_WASTE,
            "restavfall": wt.GENERAL_WASTE,
            "matavfall": wt.FOOD_WASTE,
            "grovavfall": wt.BULKY_WASTE,
            "farligtavfall": wt.HAZARDOUS,
        },
    )
