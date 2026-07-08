from typing import ClassVar, TypedDict, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, coords, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.transformers import KeyValueTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)


class _Field(TypedDict):
    """One name/value pair in the bincollectioncheck response."""

    name: str
    caption: str
    value: str


# The endpoint returns a list of collections, each a list of name/value fields
# ("type", "day", "date"). Declared here so the shape is type-checked, drives
# the offline fixtures, and raises a clear error if the provider changes it.
ResponseShape = list[list[_Field]]

# Demonstrates: alternative-input PARAMS via config_params.alternatives() (an
# address OR a lat+lon pair) + a fully declarative HttpGetRetriever whose headers
# are a callable resolved against the source's params: it geocodes the address (or
# uses the supplied coords) and bakes the point into the request headers the
# endpoint requires. validate() requires exactly one group, so no cross-field
# check is needed in __init__.

_BASE_URL = "https://www.stirling.wa.gov.au"


def _resolve_coordinates(
    address: str | None, lat: float | str | None, lon: float | str | None
) -> tuple[float, float]:
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    try:
        location = geocode(address or "")
    except ArcGisGeocodeError as e:
        raise SourceArgumentNotFound("address", address) from e
    return location["y"], location["x"]


def _headers(address=None, lat=None, lon=None, **_):
    """Build the request headers, baking in the resolved collection point."""
    lat_v, lon_v = _resolve_coordinates(address, lat, lon)
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "configid": "7c833520-7b62-4228-8522-fb1a220b32e8",
        "form": "57753bab-f589-44d7-8934-098b6d5c572f",
        "fields": f"{lon_v},{lat_v}",
        "apikeylookup": "Bin Day",
        "Origin": _BASE_URL,
        "Referer": (
            f"{_BASE_URL}/waste-and-environment/waste-and-recycling/bin-collections"
        ),
    }


@final
class Source(BaseSource):
    TITLE = "Stirling"
    DESCRIPTION = "Source for Stirling."
    URL = "https://www.stirling.wa.gov.au"
    COUNTRY = "au"
    CODEOWNERS: ClassVar[list] = ["@markvp"]
    API_URL = "https://www.stirling.wa.gov.au/bincollectioncheck/getresult"

    TEST_CASES: ClassVar[dict] = {
        "by_address": {"address": "100 Cedric Street, Stirling, WA, Australia"},
        "by_coords": {"lat": -31.9034183, "lon": 115.8320855},
        "by_coords_str": {"lat": "-31.8783052", "lon": "115.8157741"},
    }

    PARAMS = (
        alternatives(
            [text_field("address", label="Street Address")],
            [coords(lat="lat", lon="lon")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '100 Cedric Street, Stirling, WA, Australia'), "
            "or provide latitude and longitude coordinates."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(url=API_URL, headers=_headers)
    parse = parsers.JsonParser(shape=ResponseShape)

    transform = KeyValueTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "red": GENERAL_WASTE,
            "green": ORGANIC,
            "greenverge": GARDEN_WASTE,
            "yellow": RECYCLABLES,
        },
    )

    def __init__(
        self,
        address: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ):
        # validate() (in super) enforces the address-or-(lat+lon) alternative.
        super().__init__(address=address, lat=lat, lon=lon)
