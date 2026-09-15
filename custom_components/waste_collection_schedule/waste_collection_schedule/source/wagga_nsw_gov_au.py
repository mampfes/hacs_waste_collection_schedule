import datetime
from collections.abc import Iterable
from typing import ClassVar

from bs4 import Tag
from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.parsers import ArgumentGuard, HtmlParser
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service import ArcGis
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a bespoke single-council page (not a shared platform), geocoded
# through the already-shared ArcGis.geocoded_params() rather than a
# source-local implementation. The council's own frontend resolves an address
# via the Google Maps JS API and reprojects it to MGA Zone 55 client-side;
# asking ArcGIS's World Geocoding Service for outSR=28355 gets the same
# projected point directly, at rooftop/address-point precision (score 100,
# ~2-8m off the council's own tool in testing) -- good enough that x/y no
# longer need to be supplied by hand the way the legacy version of this
# source required. Only the response parsing (the council's own binDay__*
# markup) is source-specific; there is no other council on this platform to
# share it with.

API_URL = "https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day"

MGA_ZONE_55_WKID = 28355

_TYPE_MAP: dict[str, wt.WasteType] = {
    "greenWasteDetails": wt.GARDEN_WASTE,
    "domesticWasteDetails": wt.GENERAL_WASTE,
    "recyclingDetails": wt.RECYCLABLES,
}


def _describe(tag: Tag, source: "Source | None") -> Iterable[Schedule]:
    key = str(tag.get("id", ""))
    if key.startswith("binDay__"):
        key = key[len("binDay__") :]
    if key not in _TYPE_MAP:
        return

    freq_el = tag.select_one("h4")
    date_el = tag.select_one(".binDay__collectionDate")
    if freq_el is None or date_el is None:
        return

    freq = freq_el.get_text(strip=True)
    date_text = date_el.get_text(strip=True).split(" ", 1)[-1]  # e.g. "Thu 17/09/2026"
    try:
        start = datetime.datetime.strptime(date_text, "%d/%m/%Y").date()
    except ValueError:
        return

    step = recurrence.FORTNIGHTLY if "fortnight" in freq.lower() else recurrence.WEEKLY
    # Same ~6-month horizon regardless of cadence, rather than a uniform
    # occurrence count that would give weekly rounds half the lookahead of
    # fortnightly ones.
    count = 26 if step == recurrence.WEEKLY else 13
    yield Schedule(key, start, step, count)


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

    retrieve = HttpGetRetriever(
        url=API_URL,
        params=ArcGis.geocoded_params(
            "address",
            lon_param="x",
            lat_param="y",
            out_sr=MGA_ZONE_55_WKID,
            override_lon_param="x",
            override_lat_param="y",
        ),
    )
    parse = ArgumentGuard(
        HtmlParser("div.binDay__serviceDetails"),
        argument="address",
        # Note: the plain string "binDay__collectionDate" (element class) is
        # present in the page's static <style> block on every response,
        # success or failure, so it does not distinguish the two -- confirmed
        # by fetching an out-of-area address live. The rendered element's own
        # opening tag, quote included, only appears when a service section
        # actually rendered.
        contains='class="binDay__serviceDetails',
        hint=(
            "the council's site didn't return a bin day schedule for this "
            "address -- check the address is correct, or supply the 'x' and "
            "'y' MGA Zone 55 coordinates directly (see HOWTO)."
        ),
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
