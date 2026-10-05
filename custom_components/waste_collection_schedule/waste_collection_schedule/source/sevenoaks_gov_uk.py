import json
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import RowTransformer

BASE_URL = "https://sevenoaks-dc-host01.oncreate.app"
LANDING_URL = f"{BASE_URL}/w/webpage/waste-collection-day"
# Public identifiers of the "waste collection day" page and its address widget.
WEBPAGE_TOKEN = "978e3e1fd8936f98a424235001d93f261cc2458668d650a18f3a1155494d063d"
SUBPAGE_ID = "PAG0000639GBDJR1"
CELL_ID = "PCL0004972GBDJR1"

_AJAX = {"X-Requested-With": "XMLHttpRequest"}

_DATE = re.compile(r"\d{1,2} [A-Z][a-z]+ \d{4}")

_TYPE_MAP = {
    "Fortnightly garden waste collection": wt.GARDEN_WASTE,
    "Weekly recycling and general waste collection": wt.GENERAL_WASTE,
    "Weekly food waste collection": wt.FOOD_WASTE,
}


def _schedule_url(response, *keys, property_id, **_) -> str:
    """The address selection answers with a one-off URL of the schedule fragment."""
    answer = response.json()
    url = (answer.get("response") or {}).get("url")
    if answer.get("result") != "success" or not url:
        raise SourceArgumentNotFound(
            "property_id",
            property_id,
            "the address lookup did not return a schedule, please check your property_id is correct",
        )
    return url


def _next_dates(tags, source) -> list[tuple[str, str]]:
    """Pair each section heading with the first date printed beneath it.

    The page lists, per round, its heading (h4) and then "Your next collection
    date is" followed by a date such as "Thursday 08 October 2026".
    """
    rows = []
    heading = None
    for tag in tags:
        text = tag.get_text(" ", strip=True)
        if tag.name == "h4":
            heading = text if text in _TYPE_MAP else None
        elif heading is not None:
            match = _DATE.search(text)
            if match:
                rows.append((match.group(0), heading))
                heading = None
    return rows


@final
class Source(BaseSource):
    TITLE = "Sevenoaks District Council"
    DESCRIPTION = "Source for Sevenoaks District Council waste collection schedule"
    URL = "https://www.sevenoaks.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Crawshay Close TN13 3EJ": {"property_id": 51621},
        "10 Mill Lane TN14 5BX": {"property_id": 15147},
    }

    PARAMS = (text_field("property_id", "Property ID", coerce=str),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://sevenoaks-dc-host01.oncreate.app/w/webpage/waste-collection-day, "
            "enter your postcode (with the space) and select your address; the "
            "numeric property id is the `id=` value in the resulting page URL."
        ),
    }

    # 1. open the page (sets the session cookie), 2. select the address, which
    # mints a one-off schedule URL, 3. fetch that URL as the first hit.
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                LANDING_URL,
                pick=lambda response, *_, **__: None,
            ),
            retrievers.Lookup(
                LANDING_URL,
                method="POST",
                params={
                    "webpage_subpage_id": SUBPAGE_ID,
                    "webpage_token": WEBPAGE_TOKEN,
                    "widget_action": "handle_event",
                },
                data=lambda *_, property_id, **__: {
                    "code_action": "address_selected",
                    "code_params": json.dumps({"selected": str(property_id)}),
                    "action_cell_id": CELL_ID,
                    "action_page_id": SUBPAGE_ID,
                },
                headers=_AJAX,
                pick=_schedule_url,
            ),
        ),
        url=lambda *keys, **_: keys[-1],
        headers=_AJAX,
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("h4, span.value-as-text", from_json_key="data")
    preprocess = staticmethod(_next_dates)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map=_TYPE_MAP,
    )
