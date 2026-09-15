import datetime
import json
import re
from collections.abc import Iterable
from typing import Any, ClassVar

from curl_cffi.requests import Response
from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a bespoke single-council page (not a shared platform), geocoded
# through the already-shared ArcGis.geocode() rather than a source-local
# implementation. The council's own frontend resolves an address via the
# Google Maps JS API and reprojects it to MGA Zone 55 client-side; asking
# ArcGIS's World Geocoding Service for outSR=28355 gets the same projected
# point directly, at rooftop/address-point precision (score 100, ~2-8m off
# the council's own tool in testing) -- good enough that x/y no longer need
# to be supplied by hand the way the legacy version of this source required.
# Only the response parsing (the council's own binDay__* markup) is
# source-specific; there is no other council on this platform to share it
# with.

API_URL = "https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day"

_TYPE_MAP: dict[str, wt.WasteType] = {
    "greenWasteDetails": wt.GARDEN_WASTE,
    "domesticWasteDetails": wt.GENERAL_WASTE,
    "recyclingDetails": wt.RECYCLABLES,
}

_SECTION_RE = re.compile(
    r'id="binDay__(?P<key>greenWasteDetails|domesticWasteDetails|recyclingDetails)"'
    r".*?<h4[^>]*>(?P<freq>[^<]+)</h4>"
    r'.*?class="binDay__collectionDate"[^>]*>(?P<date>[^<]+)<',
    re.S,
)
_SCHEDULE_COMMENT_RE = re.compile(r'<!--\s*(\{[^}]*"schedule"[^}]*\})\s*-->', re.S)


def _query_params(
    address: str, x: float | None = None, y: float | None = None, **_: Any
) -> dict[str, Any]:
    """Resolve the request point: user-supplied x/y, else geocode the address."""
    if x is not None and y is not None:
        return {"x": x, "y": y, "address": address}
    try:
        location = geocode(address, out_sr=28355)
    except ArcGisGeocodeError as e:
        raise SourceArgumentNotFound("address", address) from e
    return {"x": location["x"], "y": location["y"], "address": address}


def _describe(record: dict, source: "Source | None") -> Iterable[Schedule]:
    step = (
        recurrence.FORTNIGHTLY
        if "fortnight" in record["freq"].lower()
        else recurrence.WEEKLY
    )
    yield Schedule(record["key"], record["date"], step, 12)


class _BinDayPageParser:
    """Parse the council's own 'What Is My Bin Day?' result page.

    Not a shared platform (Wagga is the only council on this bespoke
    markup), so this stays local to the source rather than living under
    ``service/`` -- but it is still a configured component (assigned to
    ``parse`` as an instance, not defined as a method on ``Source``), the
    same shape every other parser in this codebase takes.
    """

    def __call__(
        self, response: Response, source: "Source | None" = None
    ) -> list[dict]:
        html = response.text
        address = source.params["address"] if source is not None else None

        comment = _SCHEDULE_COMMENT_RE.search(html)
        if comment:
            data = json.loads(comment.group(1))
            if not data.get("schedule"):
                raise SourceArgumentNotFound(
                    "address",
                    address,
                    message_addition=(
                        data.get("errorMessage")
                        or "no collection schedule found for this address."
                    ),
                )

        records = []
        for match in _SECTION_RE.finditer(html):
            date_text = match.group("date").strip().split(" ", 1)[-1]
            try:
                date = datetime.datetime.strptime(date_text, "%d/%m/%Y").date()
            except ValueError:
                continue
            records.append(
                {
                    "key": match.group("key"),
                    "freq": match.group("freq").strip(),
                    "date": date,
                }
            )

        if not records:
            raise SourceArgumentNotFound(
                "address",
                address,
                message_addition=(
                    "could not parse bin day results from the page "
                    "(the council may have changed their site layout)."
                ),
            )
        return records


class Source(BaseSource):
    TITLE = "Wagga Wagga City Council"
    DESCRIPTION = "Source for Wagga Wagga City Council, NSW, Australia."
    URL = "https://wagga.nsw.gov.au"
    COUNTRY = "au"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@CozyRocket"]

    # An address outside the council's service area (or a page layout change)
    # yields no collections; surface that as an error instead of a silently
    # empty calendar.
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "24 Docker Street by address": {
            "address": "24 Docker Street, Wagga Wagga NSW",
        },
        "24 Docker Street by coordinates": {
            "address": "24 Docker Street, Wagga Wagga NSW",
            "x": 532385.29,
            "y": 6113636.31,
        },
    }

    PARAMS = (
        street_address(),
        text_field("x", "MGA Zone 55 Easting (X)", optional=True, coerce=float),
        text_field("y", "MGA Zone 55 Northing (Y)", optional=True, coerce=float),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full property address (e.g. '24 Docker Street, Wagga "
            "Wagga NSW'). This is geocoded automatically. If your address "
            "doesn't resolve correctly, you can instead supply the exact 'x' "
            "and 'y' MGA Zone 55 (GDA94, EPSG:28355) coordinates from the "
            "council's own 'What Is My Bin Day?' tool: search your address "
            "there and read them out of the URL it navigates to (it will "
            "contain 'x=...&y=...')."
        )
    }

    retrieve = HttpGetRetriever(url=API_URL, params=_query_params)
    parse = _BinDayPageParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
