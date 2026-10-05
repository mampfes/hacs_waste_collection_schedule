"""Saver (West-Brabant, NL).

The address resolves to a BAG id (``/adressen/<postcode>:<number>``). The
calendar (``/rest/adressen/<bagid>/kalender/<year>``) only carries numeric
waste-stream ids, so the stream list (``/rest/adressen/<bagid>/afvalstromen``)
is fetched alongside it and the preprocessor joins the two.
"""

from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

_API_BASE = "https://saver.nl"
_HEADERS = {"Accept": "application/json"}
_STREAMS = "streams"


def _postcode(value: str) -> str:
    return str(value).replace(" ", "").upper()


def _suffix(entry: dict) -> str:
    return f"{entry.get('huisletter') or ''}{entry.get('toevoeging') or ''}"


def _pick_bagid(response, *, postcode: str, toevoeging: str = "", **_) -> str:
    data = response.json()
    if not data:
        raise SourceArgumentNotFound("postcode", _postcode(postcode))

    target = str(toevoeging or "").strip()
    if len(data) == 1 and not target:
        return data[0]["bagid"]
    for entry in data:
        if _suffix(entry).casefold() == target.casefold():
            return entry["bagid"]
    raise SourceArgumentNotFoundWithSuggestions(
        "toevoeging", target, [_suffix(entry).strip() or "(none)" for entry in data]
    )


def _targets(source: BaseSource, bagid: str) -> list:
    today = date.today()
    years = [today.year]
    if today.month >= 11:
        years.append(today.year + 1)
    return [_STREAMS, *years]


def _target_url(target: Any, bagid: str, **_) -> str:
    if target == _STREAMS:
        return f"{_API_BASE}/rest/adressen/{bagid}/afvalstromen"
    return f"{_API_BASE}/rest/adressen/{bagid}/kalender/{target}"


def _rows(records: Any, source: BaseSource | None = None) -> list[tuple[str, str]]:
    """Join the calendar entries to the stream titles listed beside them."""
    titles: dict[int, str] = {}
    for item in records or []:
        stream_id = item.get("id")
        if stream_id is None:
            continue
        title = (item.get("menu_title") or item.get("title") or "").strip()
        if title:
            titles[stream_id] = title

    rows: list[tuple[str, str]] = []
    for item in records or []:
        stream_id = item.get("afvalstroom_id")
        date_str = item.get("ophaaldatum")
        if not stream_id or not date_str:
            continue
        rows.append((date_str, titles.get(stream_id, f"Stream {stream_id}")))
    return rows


@final
class Source(BaseSource):
    TITLE = "Saver"
    DESCRIPTION = (
        "Source for Saver waste collection in West-Brabant (Roosendaal, "
        "Halderberge, Bergen op Zoom, Rucphen, Zundert, Steenbergen, Woensdrecht)."
    )
    URL = "https://saver.nl"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Roosendaal Eikenlaan 1": {"postcode": "4702AA", "huisnummer": 1},
        "Oudenbosch Voorzet 1": {"postcode": "4731XR", "huisnummer": "1"},
        "St. Willebrord Weberstraat 1": {"postcode": "4711AA", "huisnummer": 1},
    }

    PARAMS = (
        postcode(postcode_field="postcode", house_field="huisnummer"),
        text_field("toevoeging", "Addition", default=""),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the same postcode and house number you would enter at "
            "https://saver.nl/afvalkalender. If your address has a letter or "
            "addition (e.g. '5a'), provide the letter/addition in the "
            "'toevoeging' argument."
        ),
        "nl": (
            "Gebruik dezelfde postcode en huisnummer als je zou invoeren op "
            "https://saver.nl/afvalkalender. Als je adres een letter of "
            "toevoeging heeft (bijv. '5a'), geef dan de letter/toevoeging in "
            "het 'toevoeging'-argument."
        ),
    }

    # One response for the stream list, then one calendar per year (next year
    # too from November), all for the BAG id the address resolves to.
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            lambda postcode, huisnummer, **_: (
                f"{_API_BASE}/adressen/{_postcode(postcode)}:{str(huisnummer).strip()}"
            ),
            headers=_HEADERS,
            pick=_pick_bagid,
        ),
        targets=_targets,
        fetch=retrievers.Request(_target_url, headers=_HEADERS),
    )

    parse = parsers.EachResponse(parsers.JsonParser())

    preprocess = staticmethod(_rows)

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "GFT+E": wt.ORGANIC,
            "Restafval": wt.GENERAL_WASTE,
            "Papier": wt.PAPER,
            "Glas": wt.GLASS,
            "PMD": wt.RECYCLABLES,
            "PBD / PMD (zakken)": wt.RECYCLABLES,
            "Textiel": wt.TEXTILES,
        },
    )
