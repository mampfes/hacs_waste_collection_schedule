"""Obec Popůvky (Brno-venkov), Czech Republic.

Composes: :class:`~waste_collection_schedule.retrievers.FanOutRetriever`. The
municipality's calendar page lists its collection routes in a ``<select>`` and
embeds the id of the calendar widget in a script; both resolve once
(``prepare``). The widget then serves one month of the calendar per request, so
the fan-out fetches the current month and the twelve after it. Every collection
is a tooltip block whose id carries the date and whose ``<dt>`` entries name the
waste types. The month grid also renders a few days of the neighbouring months,
which the next request repeats, so the records are deduplicated.
"""

import datetime
import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    date_parsers,
    parsers,
    preprocessors,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

_PAGE_URL = "https://www.popuvky.cz/obec/terminy-svozu/"
_API_URL = "https://www.popuvky.cz/modules/communal_services/ax_calendar.php"

# The current month plus twelve more: a full rolling year.
_MONTHS_TO_FETCH = 13

_ACTIVE_RE = re.compile(r"active:\s*(\d+)")


def _place_and_widget(response, *, place: str, **_) -> tuple[str, str]:
    """The route's id and the calendar widget's id, both read off the page."""
    match = _ACTIVE_RE.search(response.text)
    if match is None:
        raise ValueError("Could not find the calendar widget id on the Popůvky page")
    soup = BeautifulSoup(response.text, "html.parser")
    select = soup.find("select", {"name": "communal_place"})
    places: dict[str, str] = {}
    if select:
        for option in select.find_all("option"):
            name = option.get_text(strip=True)
            value = option.get("value")
            if name and value:
                places[name] = value
    for name, value in places.items():
        if name.casefold() == place.strip().casefold():
            return value, match.group(1)
    raise SourceArgumentNotFoundWithSuggestions("place", place, list(places))


def _months(source, context) -> list[tuple[int, int]]:
    today = datetime.date.today()
    index = today.year * 12 + today.month - 1
    return [divmod(index + offset, 12) for offset in range(_MONTHS_TO_FETCH)]


def _month_params(target, context, **_) -> dict:
    year, zero_based_month = target
    place_id, widget_id = context
    return {
        "communal_month": zero_based_month + 1,
        "communal_year": year,
        "active": widget_id,
        "communal_place": place_id,
        "communal_waste": 0,
    }


@final
class Source(BaseSource):
    TITLE = "Popůvky"
    DESCRIPTION = (
        "Source for the municipal waste collection calendar of Popůvky, Czech Republic."
    )
    URL = "https://www.popuvky.cz/obec/terminy-svozu/"
    COUNTRY = "cz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Popůvky (Brno-venkov)": {"place": "Popůvky (Brno-venkov)"},
        "Popůvky - chatová oblast": {"place": "Popůvky - chatová oblast"},
    }

    PARAMS = (text_field("place", label="Collection area"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the collection calendar page and note which collection route "
            "matches your address: 'Popůvky (Brno-venkov)' for the village itself, "
            "or 'Popůvky - chatová oblast' for the cottage/recreational area."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PLASTIC,
        wt.ORGANIC,
    ]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_PAGE_URL, pick=_place_and_widget),
        targets=_months,
        fetch=retrievers.Request(_API_URL, params=_month_params),
    )

    parse = parsers.EachResponse(
        parsers.HtmlParser('div[id^="com-tooltip"] dt'),
    )

    preprocess = preprocessors.Deduplicate(
        key=lambda dt: (dt.find_parent("div")["id"], dt.get_text(" ", strip=True))
    )

    transform = HtmlTransformer(
        date_getter=lambda dt: dt.find_parent("div")["id"].removeprefix("com-tooltip"),
        type_getter=lambda dt: dt.get_text(" ", strip=True),
        parse_date=date_parsers.for_format("%Y%m%d"),
        type_value_map={
            "Komunální odpad": wt.GENERAL_WASTE,
            "Plasty od domu": wt.PLASTIC,
            "Papír": wt.PAPER,
            "Sklo": wt.GLASS,
            "BIO odpad od domu": wt.ORGANIC,
        },
    )
