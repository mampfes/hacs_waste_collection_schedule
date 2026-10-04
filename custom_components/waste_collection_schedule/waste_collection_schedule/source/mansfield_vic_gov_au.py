import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.mansfield.vic.gov.au"

_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")


def _normalise(value: str) -> str:
    return " ".join(value.split()).lower()


def _pick_address(response, *keys, street_address, **_) -> str:
    """The autocomplete answers ``[{"value": address, ...}, ...]``.

    The council stores its addresses with doubled spaces ("3 Curia Street
    MANSFIELD  VIC  3722"), and the schedule only answers to that exact spelling.
    """
    hits = [
        hit["value"]
        for hit in response.json()
        if isinstance(hit, dict) and hit.get("value")
    ]
    wanted = _normalise(street_address)
    for hit in hits:
        if _normalise(hit) == wanted:
            return hit
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", street_address, [" ".join(hit.split()) for hit in hits]
    )


def _services(command, source) -> list[dict]:
    """One row per service of the schedule HTML an ``insert`` command carries."""
    if not isinstance(command, dict) or command.get("command") != "insert":
        return []
    html = command.get("data")
    if not isinstance(html, str):
        return []
    rows = []
    for heading in BeautifulSoup(html, "html.parser").find_all("h4"):
        info = heading.find_next_sibling("div", class_="info")
        match = _DATE.search(info.get_text(" ", strip=True)) if info else None
        if match:
            rows.append({"type": heading.get_text(" ", strip=True), "date": match[0]})
    return rows


@final
class Source(BaseSource):
    TITLE = "Mansfield Shire Council"
    DESCRIPTION = "Source for Mansfield Shire Council rubbish collection."
    URL = "https://www.mansfield.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mansfield Zoo": {
            "street_address": "1064 Mansfield-Woods Point Road MANSFIELD VIC 3722"
        },
        "Ambulance Station": {"street_address": "3 Curia Street MANSFIELD VIC 3722"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address on the "
            "[Mansfield Shire Council bin day page](https://www.mansfield.vic.gov.au/community/residents/waste-recycling/check-my-bin-day) "
            "and enter it as shown in the autocomplete result, e.g. "
            "'3 Curia Street MANSFIELD VIC 3722'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/views-autocomplete-filters/waste_schedule/block_1/formatted_address/0",
                # The autocomplete finds nothing for a whole address (it holds
                # doubled spaces); the street number and first word do find it.
                params=lambda street_address, **_: {
                    "q": " ".join(street_address.split()[:2])
                },
                headers={"Accept": "application/json"},
                pick=_pick_address,
            ),
        ),
        url=f"{API}/views/ajax",
        params=lambda key, **_: {
            "_wrapper_format": "drupal_ajax",
            "view_name": "waste_schedule",
            "view_display_id": "block_1",
            "view_args": "",
            "view_path": "/node/96",
            "view_base_path": "waste-schedule",
            "formatted_address": key,
        },
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )

    parse = parsers.JsonParser()

    preprocess = ExplodeList(_services)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "General waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Bin": wt.GARDEN_WASTE,
        },
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
