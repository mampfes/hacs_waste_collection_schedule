"""The Hills address cascade declared with shared request and lookup steps."""

from waste_collection_schedule import lookups
from waste_collection_schedule.retrievers import Lookup, Request

API_URL = "https://apps.thehills.nsw.gov.au/seamlessproxy/api"


def _normalize(value) -> str:
    return str(value).strip().upper().replace(" ", "")


def _suburb(response, *, suburb, **_):
    mapping = {_normalize(row["Suburb"]): row["SuburbKey"] for row in response.json()}
    return lookups.resolve(mapping, suburb, argument="suburb", normalize=_normalize)


def _street(response, _suburb_key, *, street, **_):
    mapping = {_normalize(row["Street"]): row["StreetKey"] for row in response.json()}
    return lookups.resolve(mapping, street, argument="street", normalize=_normalize)


def _property(response, _suburb_key, _street_key, *, houseNo, **_):
    mapping = {
        _normalize(str(int(row["HouseNo"])) + row.get("HouseSuffix", "").strip()): row[
            "PropertyKey"
        ]
        for row in response.json()
    }
    return lookups.resolve(mapping, houseNo, argument="houseNo", normalize=_normalize)


calendar_retriever = Request(
    lambda suburb_key, street_key, property_key, **_: (
        f"{API_URL}/services/{property_key}"
    ),
    before=(
        Lookup(f"{API_URL}/suburbs/get", pick=_suburb),
        Lookup(lambda suburb_key, **_: f"{API_URL}/streets/{suburb_key}", pick=_street),
        Lookup(
            f"{API_URL}/properties/GetPropertiesByStreetAndSuburbKey",
            params=lambda suburb_key, street_key, **_: {
                "streetkey": street_key,
                "suburbKey": suburb_key,
            },
            pick=_property,
        ),
    ),
)
