"""Erlensee (Hesse, Germany).

Demonstrates ``IcsSessionRetriever`` for a reminder form whose submission *is*
the calendar: the first step reads the form's own street list and event-type
checkboxes, the second POSTs the chosen street plus every event type back and
answers with the ICS download, so ``feed_url`` stays ``None`` and the last step's
response is what the parser reads. The download is a rolling six-month window
rather than a per-year calendar, hence ``lookahead_month=None``.

Every summary carries the street as a suffix ("Restmüll (MT) (Am Rathaus)"),
which ``RowRelabel(strip=...)`` removes. Only that trailing group may go: the
waste type itself can contain parentheses, and so can the street
("Oberhörr (Sandhof / Sonnenhof)").
"""

from typing import Any, ClassVar, final
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import RowRelabel
from waste_collection_schedule.service.ICS import (
    IcsFeedsParser,
    IcsSessionRetriever,
    resolve_select_option,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://sperrmuell.erlensee.de/"

# "timeframe" option 46 = "6 Monate" (rolling six month window, not year bound)
_TIMEFRAME = 46

# The trailing "(<street>)" group of a summary: one parenthesised group at the
# very end, allowing one level of nesting inside it because a street can carry
# its own parentheses ("Oberhörr (Sandhof / Sonnenhof)"). It is the *last*
# group only, so a waste type's own "(MT)" survives.
_STREET_SUFFIX = r"\s*\((?:[^()]|\([^()]*\))*\)\s*$"


def _reminder_form(response: Any, context: "dict[str, Any]") -> "dict[str, Any]":
    """The configured street's id and every event type the form offers."""
    soup = BeautifulSoup(response.text, "html.parser")
    streets: dict[str, int] = {}
    select = soup.find("select", {"id": "street"})
    if select:
        for option in select.find_all("option"):
            value = option.get("value")
            if value:
                streets[option.get_text(strip=True)] = int(str(value))
    name = resolve_select_option("street", str(context["street"]), list(streets))
    event_ids = [
        int(str(box["value"]))
        for box in soup.find_all("input", {"name": "eventType[]"})
        if box.get("value")
    ]
    return {"street_id": streets[name], "street_name": name, "event_ids": event_ids}


def _reminder_download(street_id: int, event_ids: "list[int]", **_: Any) -> str:
    return urlencode(
        [
            ("street", street_id),
            ("timeframe", _TIMEFRAME),
            ("download", "ical"),
            *(("eventType[]", event_id) for event_id in event_ids),
        ]
    )


@final
class Source(BaseSource):
    TITLE = "Erlensee"
    DESCRIPTION = "Source for waste collection in Erlensee, Hessen."
    URL = _URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@SgtSeppel"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Am Rathaus": {"street": "Am Rathaus"},
        "Am Haspel": {"street": "Am Haspel"},
        "Oberhörr (Sandhof / Sonnenhof)": {"street": "Oberhörr (Sandhof / Sonnenhof)"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "Nirgendwostraße"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": f"Go to {_URL} and look up the exact street name in the dropdown.",
        "de": (
            f"Öffnen Sie {_URL} und entnehmen Sie den Straßennamen aus der "
            "Auswahlliste."
        ),
    }

    PARAMS = (street(),)

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": _URL,
                "params": {"type": "reminder"},
                "extract": _reminder_form,
            },
            {
                "method": "POST",
                "url": _URL,
                "params": {"type": "reminder"},
                "data": _reminder_download,
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            },
        ],
        feed_url=None,
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    preprocess = RowRelabel(strip=_STREET_SUFFIX)

    # "Restmüll" and "Restmüll (MT)" (and the two garden collections) are
    # different rounds that resolve to one canonical type, so the raw label is
    # kept as the description.
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Restmüll (MT)": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Papier": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Gartenabfälle": wt.GARDEN_WASTE,
            "Gartenabfall-Straßensammlung": wt.GARDEN_WASTE,
            "Sondermüll": wt.HAZARDOUS,
        },
        carry_raw_label=True,
    )
