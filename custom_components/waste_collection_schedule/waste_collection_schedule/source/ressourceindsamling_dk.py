import datetime
import urllib.parse
import zoneinfo
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

API = "https://selfserviceapi.waste2x.dk/api"
ZONE = "Europe/Copenhagen"
HEADERS = {"organizationid": "76fbcd50-996e-4b0e-8b5b-3e9e49cea6d6"}


def _pick_customer(response, streetName: str, number: str, **_) -> int:
    """The customer id of the address; the exact "street number," hit wins."""
    items = response.json().get("items") or []
    if not items:
        raise SourceArgumentNotFound("streetName", f"{streetName} {number}")
    wanted = f"{streetName} {number},".lower()
    for item in items:
        if str(item.get("location", "")).lower().startswith(wanted):
            return item["customerId"]
    return items[0]["customerId"]


def _search_url(streetName: str, number: str, **_) -> str:
    # the trailing % is a wildcard the search needs
    return f"{API}/Customer/Customer/SearchCustomer/" + urllib.parse.quote(
        f"{streetName} {number}".lower() + "%"
    )


def _services_url(customer_id: int, **_) -> str:
    # the API refuses a window longer than 31 days, so the end is 31 elapsed
    # days on (not 31 calendar days, which is 31 days and an hour across DST);
    # it starts at today's local midnight so the request is the same all day
    zone = zoneinfo.ZoneInfo(ZONE)
    start = datetime.datetime.now(zone).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = (start.astimezone(datetime.UTC) + datetime.timedelta(days=31)).astimezone(
        zone
    )
    window = "/".join(
        t.replace(microsecond=0).isoformat(timespec="milliseconds")
        for t in (start, end)
    )
    return f"{API}/Services/Services/GetServicesForCustomer/{customer_id}/{window}"


@final
class Source(BaseSource):
    TITLE = "RessourceIndsamling.dk"
    DESCRIPTION = "Source for RessourceIndsamling.dk collection"
    URL = "https://www.ressourceindsamling.dk/"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True

    # What the recorded cassette produces; Juletræer (Christmas trees) is
    # mapped too but is only collected in January.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.METAL,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"streetName": "Kløvertoften", "number": "61"},
    }

    PARAMS = (street(field="streetName"), house_number(field="number"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and house number as they appear on "
            "https://www.ressourceindsamling.dk/ (for example Kløvertoften and 61)."
        ),
    }

    # A bin with two chambers ("Mad/Rest") is two collections on one day.
    _TYPE_MAP: ClassVar[dict] = {
        "Mad/Rest": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
        "Mad/Rest affald": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
        "Haveaffald": wt.GARDEN_WASTE,
        "Juletræer": wt.GARDEN_WASTE,
        "Storskrald": wt.BULKY_WASTE,
        "Pap": wt.PAPER,
        "Papir/Plast & MDK": [wt.PAPER, wt.PLASTIC],
        "Metal/Glas affald": [wt.METAL, wt.GLASS],
        "Metal/Glas": [wt.METAL, wt.GLASS],
        "Farligt affald": wt.HAZARDOUS,
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_search_url, headers=HEADERS, pick=_pick_customer),),
        url=_services_url,
        headers=HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser()

    # The API stamps a collection day as [local midnight, next local midnight)
    # in UTC, so the day is the start's date on the Copenhagen clock.
    transform = JsonTransformer(
        date_key="startTime",
        type_key="serviceTypePublicName",
        parse_date=date_parsers.in_timezone(ZONE),
        type_value_map=_TYPE_MAP,
    )
