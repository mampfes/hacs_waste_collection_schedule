import json
import re
from datetime import UTC, date, datetime
from typing import ClassVar, NamedTuple, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

_CALENDAR_URL = "https://hassleholmmiljo.se/privat/sophamtning/tomningskalender"
_API_URL = "https://api-universal.appbolaget.se/@universal/waste/properties"

_STATE_RE = re.compile(
    r"AppRegistry\.registerInitialState\([^,]+,(\{.*?\})\);", re.DOTALL
)
_UNIT_RE = re.compile(r"unit=([0-9a-f-]{36})")
_TIMEZONE = ZoneInfo("Europe/Stockholm")


class _Property(NamedTuple):
    """The two ids the calendar page hands the schedule API."""

    property_id: str
    unit: str


def _read_calendar_page(response, alias, **_) -> _Property:
    """Read the property id and unit UUID off the calendar page's embedded state."""
    for block in _STATE_RE.findall(response.text):
        try:
            state = json.loads(block)
        except ValueError:
            continue
        month = state.get("calendarMonth")
        if not month:
            continue
        customers = month.get("customers")
        property_id = month.get("property") or (customers[0] if customers else None)
        unit = _UNIT_RE.search(month.get("pdfUrl", ""))
        if property_id and unit:
            return _Property(property_id, unit.group(1))
    raise SourceArgumentNotFound("alias", alias)


def _local_date(timestamp: str) -> date:
    """The API stores collection times in UTC: 22:00 UTC is the next local day."""
    return (
        datetime.fromisoformat(timestamp).replace(tzinfo=UTC).astimezone(_TIMEZONE)
    ).date()


def _label(record) -> str:
    code = record["code"] or {}
    return code.get("description") or code.get("code") or "Unknown"


@final
class Source(BaseSource):
    TITLE = "Hässleholm Miljö"
    DESCRIPTION = "Source for waste collection schedules from Hässleholm Miljö, Sweden."
    URL = "https://hassleholmmiljo.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Tyringevägen 24, Finja": {"alias": "hmab-tyringevaegen-24-finja"},
    }

    PARAMS = (text_field("alias", "Alias"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://hassleholmmiljo.se/privat/sophamtning/tomningskalender, "
            "search for your address and select it. Copy the `alias` value from "
            "the URL (`?alias=hmab-...`), for example "
            "`hmab-tyringevaegen-24-finja`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _CALENDAR_URL,
                params=lambda alias, **_: {"alias": alias},
                pick=_read_calendar_page,
            ),
        ),
        url=lambda prop, **_: f"{_API_URL}/{prop.property_id}/",
        params=lambda prop, **_: {"unit": prop.unit},
        raise_for_status=True,
    )
    parse = parsers.JsonParser("data", "services")
    preprocess = ExplodeList("collections", into="collection")
    transform = JsonTransformer(
        date_key=lambda record: _local_date(record["collection"]["collection_at"]),
        type_key=_label,
        carry_raw_label=True,
        type_value_map={
            # "Fyrfack kärl 1": plast- och pappersförpackningar
            "Kärl1": [wt.RECYCLABLES, wt.PAPER],
            # "Fyrfack kärl 2": restavfall och returpapper
            "Kärl2": [wt.GENERAL_WASTE, wt.PAPER],
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            # "Budad hämtning": fee for emptying the four-compartment bin
            "Budad hämtning": wt.OTHER,
        },
    )
