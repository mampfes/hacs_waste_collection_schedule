"""Stadt Verl (verl.de).

A "scrape a page for a one-time middleware key, then POST the district
selection to a dynamically-keyed endpoint" shape. The calendar page embeds a
``middlewareKey`` (and a hidden page id) that must be read out of the HTML
before the ICS-generating POST can be addressed. That read is the lookup step
below; the shared ``LookupChainRetriever`` then puts the key in the endpoint's
query string and POSTs the district selection to it.
"""

import re
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_CALENDAR_URL = (
    "https://www.verl.de/service/abfallentsorgung/umwelt-und-abfallkalender.html"
)
_ENDPOINT_PATH = "/?middlewareAction=createWastecalendarIcs"
_BASE_URL = "https://www.verl.de"

_KEY_RE = re.compile(r"middlewareKey=([A-Za-z0-9]+)")
_PAGE_ID_RE = re.compile(r'name="id"\s+value="(\d+)"')


class _CalendarPage(NamedTuple):
    """The two one-time ids the calendar page hands the ICS endpoint.

    Both come out of the same page, so they resolve as one lookup step rather
    than two: a second step would mean a second identical GET.
    """

    middleware_key: str
    page_id: str


def _read_calendar_page(source: BaseSource, keys: tuple) -> _CalendarPage:
    """Read the middleware key and hidden page id off the calendar page."""
    resp = source.session.get(_CALENDAR_URL)
    resp.raise_for_status()

    key_match = _KEY_RE.search(resp.text)
    if not key_match:
        raise SourceArgumentNotFound(
            "bezirk",
            int(source.params["bezirk"]),
            "could not find middleware key on Verl calendar page",
        )

    page_id_match = _PAGE_ID_RE.search(resp.text)
    return _CalendarPage(
        key_match.group(1), page_id_match.group(1) if page_id_match else "50"
    )


@final
class Source(BaseSource):
    TITLE = "Stadt Verl"
    DESCRIPTION = "Source for Stadt Verl waste collection."
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Abfuhrbezirk 1": {"bezirk": 1},
        "Abfuhrbezirk 3": {"bezirk": 3},
        "Abfuhrbezirk 5": {"bezirk": 5},
    }

    PARAMS = (
        dropdown(
            "bezirk",
            options=["1", "2", "3", "4", "5"],
            label="Collection district",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Your collection district number (1-5). Find yours at "
            "https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke"
        ),
        "de": (
            "Ihre Abfuhrbezirksnummer (1-5). Ermitteln Sie Ihren Bezirk unter "
            "https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke"
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(_read_calendar_page,),
        url=lambda page, **_: (
            f"{_BASE_URL}{_ENDPOINT_PATH}&middlewareKey={page.middleware_key}"
        ),
        method="POST",
        data=lambda page, bezirk, **_: {
            "id": page.page_id,
            f"bezirk{int(bezirk)}": "on",
            "abfall1": "on",
            "abfall2": "on",
            "abfall3": "on",
            "abfall4": "on",
            "abfuhr_tag": "0",
            "individuell": "Auswahl laden",
        },
        headers={"Referer": _CALENDAR_URL},
    )
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "restmülltonne": wt.GENERAL_WASTE,
            "restmülltonne/mögliche zusatzleerung": wt.GENERAL_WASTE,
            "komposttonne": wt.ORGANIC,
            "papiertonne": wt.PAPER,
            "gelbe tonne": wt.RECYCLABLES,
            "gartenabfallannahme": wt.GARDEN_WASTE,
            "wertstoffhof": wt.RECYCLABLES,
            "giftmobil": wt.HAZARDOUS,
        }
    )

    def __init__(self, bezirk: "int | str"):
        super().__init__(bezirk=str(bezirk))
