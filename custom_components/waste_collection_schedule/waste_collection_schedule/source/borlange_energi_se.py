import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.transformers import JsonTransformer

_BASE = "https://www.borlange-energi.se"
_PAGE_URL = f"{_BASE}/avfall-och-atervinning/sophamtning"

# The "När kommer sopbilen?" widget on the waste page is a Sitevision app
# (applicationId "se.soleil.garbageTruckFetcher"). Its data comes from
# <BASE>/appresource/<page_id>/<portlet_id>/getcontainerdata. Both ids are
# Sitevision-internal and reassigned whenever the page or the widget placement
# is rebuilt (GitHub issue #7249), so they are read off the live page.
_PORTLET_ID = re.compile(
    r"applicationId:'se\.soleil\.garbageTruckFetcher\|[^']*'.*?portletId:'([^']+)'"
)
_PAGE_ID = re.compile(r"/webapp-resource/([^/\"']+)/")

# "Tömning torsdag 8 oktober", or "Tömning idag" / "Tömning imorgon" around the day.
_DAY_MONTH = re.compile(r"(\d{1,2})\s+([a-zåäö]+)")
_TODAY = re.compile(r"\bi\s?dag\b")
_TOMORROW = re.compile(r"\bi\s?morgon\b")


def _collection_endpoint(response, **_) -> str:
    """The widget's ``getcontainerdata`` URL, from the ids on the waste page."""
    portlet = _PORTLET_ID.search(response.text)
    page = _PAGE_ID.search(response.text)
    if not portlet or not page:
        raise ValueError(
            "Could not locate the waste collection widget on the Borlänge "
            "Energi website; the page layout may have changed"
        )
    return f"{_BASE}/appresource/{page.group(1)}/{portlet.group(1)}/getcontainerdata"


def _day_month(record) -> str:
    """The record's date as ``"<day> <month number>"``; the year is not published."""
    text = str(record["disposalDay"]).lower()
    today = datetime.date.today()
    if _TODAY.search(text):
        return f"{today.day} {today.month}"
    if _TOMORROW.search(text):
        tomorrow = today + datetime.timedelta(days=1)
        return f"{tomorrow.day} {tomorrow.month}"
    match = _DAY_MONTH.search(text)
    month = recurrence.month(match.group(2)) if match else None
    if not match or month is None:
        raise ValueError(f"Unrecognized date format: {record['disposalDay']}")
    return f"{int(match.group(1))} {month}"


@final
class Source(BaseSource):
    TITLE = "Borlänge Energi"
    DESCRIPTION = "Waste collection schedule for Borlänge, Sweden"
    URL = _PAGE_URL
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mats Knuts Väg": {"pickup_address": "Mats Knuts Väg 100"},
        "Rorsmans Väg 7": {"pickup_address": "Rorsmans Väg 7"},
    }

    PARAMS = (street_address("pickup_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your pickup address as it appears in the 'När kommer "
            "sopbilen?' search on the [Borlänge Energi waste page]"
            f"({_PAGE_URL}), e.g. `Mats Knuts Väg 100`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_PAGE_URL, pick=_collection_endpoint),),
        url=lambda endpoint, **_: endpoint,
        params=lambda endpoint, pickup_address, **_: {"pickupAddress": pickup_address},
        raise_for_status=True,
    )

    parse = parsers.JsonParser()

    # The widget names the weekday, day and month but never the year: the next
    # such date on or after today.
    transform = JsonTransformer(
        date_key=_day_month,
        type_key="contentType",
        type_value_map={
            "Matavfall": wt.FOOD_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Pappersförpackningar": wt.PAPER,
            "Plastförpackningar": wt.RECYCLABLES,
        },
        parse_date=date_parsers.next_weekday("%d %m"),
    )
