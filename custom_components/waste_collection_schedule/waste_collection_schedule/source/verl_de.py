"""Stadt Verl (verl.de).

Demonstrates: a "scrape a page for a one-time middleware key, then POST the
district selection to a dynamically-keyed endpoint" shape. The calendar page
embeds a ``middlewareKey`` (and a hidden page id) that must be read out of the
HTML before the ICS-generating POST can be addressed, so no configured
retriever expresses this in one declaration; hence a source-defined
retrieve().
"""

import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_CALENDAR_URL = (
    "https://www.verl.de/service/abfallentsorgung/umwelt-und-abfallkalender.html"
)
_ENDPOINT_PATH = "/?middlewareAction=createWastecalendarIcs"
_BASE_URL = "https://www.verl.de"

_KEY_RE = re.compile(r"middlewareKey=([A-Za-z0-9]+)")
_PAGE_ID_RE = re.compile(r'name="id"\s+value="(\d+)"')


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

    def retrieve(self, source):
        session = source.session
        bezirk = int(source.params["bezirk"])

        resp = session.get(_CALENDAR_URL)
        resp.raise_for_status()

        key_match = _KEY_RE.search(resp.text)
        if not key_match:
            raise SourceArgumentNotFound(
                "bezirk", bezirk, "could not find middleware key on Verl calendar page"
            )
        middleware_key = key_match.group(1)

        page_id_match = _PAGE_ID_RE.search(resp.text)
        page_id = page_id_match.group(1) if page_id_match else "50"

        endpoint = f"{_BASE_URL}{_ENDPOINT_PATH}&middlewareKey={middleware_key}"
        data = {
            "id": page_id,
            f"bezirk{bezirk}": "on",
            "abfall1": "on",
            "abfall2": "on",
            "abfall3": "on",
            "abfall4": "on",
            "abfuhr_tag": "0",
            "individuell": "Auswahl laden",
        }

        return session.post(endpoint, data=data, headers={"Referer": _CALENDAR_URL})

    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "restmülltonne": GENERAL_WASTE,
            "restmülltonne/mögliche zusatzleerung": GENERAL_WASTE,
            "komposttonne": ORGANIC,
            "papiertonne": PAPER,
            "gelbe tonne": RECYCLABLES,
            "gartenabfallannahme": GARDEN_WASTE,
            "wertstoffhof": RECYCLABLES,
            "giftmobil": HAZARDOUS,
        }
    )

    def __init__(self, bezirk: "int | str"):
        super().__init__(bezirk=str(bezirk))
