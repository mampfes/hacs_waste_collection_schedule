from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

ADDRESS_SUGGEST_URL = "https://opendata.ccc.govt.nz/CCCSearch/rest/address/suggest"
BIN_SERVICE_URL = (
    "https://ccc-data-citizen-api-v1-prod.au-s1.cloudhub.io/api/v1/properties/{}"
)
OVERRIDES_URL = "https://ccc.govt.nz/api/kerbsidedateoverrides"

# The public client credentials of the council's own bin-day lookup.
BINS_HEADERS = {
    "client_id": "69f433c880c74c349b0128e9fa1b6a93",
    "client_secret": "139F3D2A83E34AdF98c80566f2eb7212",
}
# Rounds the property has that are not kerbside collections.
_NOT_COLLECTED = ("Daily", "Not Collected")


def _rating_unit(response, address, **_):
    """A property's bins hang off its rating unit, not its street address."""
    matches = response.json()
    if not matches:
        raise SourceArgumentNotFound(
            "address", address, "Check the address on https://ccc.govt.nz"
        )
    return matches[0]["RatingUnitID"]


def _is_waf_challenge(response):
    """The council site answers a cookie-less first hit with an Incapsula page."""
    return "json" not in response.headers.get("Content-Type", "")


def _collections(record, _source):
    """The property's current rounds, moved by the council's holiday overrides.

    The API keeps every round it ever planned and flags the superseded ones
    with ``out_of_date``: only the current ones are published. A round whose
    only date is stale is dropped rather than rolled forward, since its next
    date is not known.
    """
    moved = {
        override["OriginalDate"]: override["NewDate"]
        for override in record["overrides"] or []
    }
    rows = []
    for collection in record["property"]["bins"]["collections"]:
        if str(collection.get("out_of_date")).lower() != "false":
            continue
        if collection.get("pick_up_group") in _NOT_COLLECTED:
            continue
        planned = collection["next_planned_date_app"]
        rows.append(
            {"date": moved.get(planned, planned), "material": collection["material"]}
        )
    return rows


@final
class Source(BaseSource):
    TITLE = "Christchurch City Council"
    DESCRIPTION = "Source for Christchurch City Council."
    URL = "https://ccc.govt.nz"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "53 Hereford Street": {"address": "53 Hereford Street"}
    }
    PARAMS = (street_address(),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the council's bin-day lookup on "
            "https://ccc.govt.nz finds it, e.g. 53 Hereford Street. Only the dates the council currently "
            "plans are shown; a round the council has no current date for is left out. "
            "Since the v3 pipeline migration, waste types use canonical, localised "
            "names. Update filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            ADDRESS_SUGGEST_URL,
            params=lambda address, **_: {
                "q": address,
                "status": "current",
                "crs": "epsg:4326",
                "limit": 1,
            },
            pick=_rating_unit,
        ),
        targets=lambda source, rating_unit: ("property", "overrides"),
        fetch=retrievers.Request(
            lambda target, rating_unit, **_: (
                BIN_SERVICE_URL.format(rating_unit)
                if target == "property"
                else OVERRIDES_URL
            ),
            headers=lambda target, rating_unit, **_: (
                BINS_HEADERS if target == "property" else {"Accept": "application/json"}
            ),
            retry_if=_is_waf_challenge,
        ),
    )
    parse = parsers.NamedResponses(
        {"property": parsers.JsonParser(), "overrides": parsers.JsonParser()}
    )
    preprocess = preprocessors.Compose(
        preprocessors.ExplodeList(_collections),
        preprocessors.Deduplicate(key=lambda row: (row["date"], row["material"])),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="material",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Organic": wt.ORGANIC,
        },
    )
