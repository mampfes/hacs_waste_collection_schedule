import logging
from dataclasses import replace
from typing import TypedDict, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.transformers import KeyValueTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

_LOGGER = logging.getLogger(__name__)


class _Field(TypedDict):
    """One name/value pair in the bincollectioncheck response."""

    name: str
    caption: str
    value: str


# The endpoint returns a list of collections, each a list of name/value fields
# ("type", "day", "date"). Declared here so the shape is type-checked, drives
# the offline fixtures, and raises a clear error if the provider changes it.
ResponseShape = list[list[_Field]]

# Demonstrates: alternative-input PARAMS (address OR lat+lon) + a source that
# overrides retrieve() to compute request headers from its params before
# delegating to the zero-config http_get retriever.
#
# Because either group satisfies the source, both params are marked
# required=False and the cross-field check lives in __init__.
_PARAMS_ADDRESS = replace(text_field("address", label="Street Address"), required=False)
_PARAMS_COORDS = replace(coords(lat="lat", lon="lon"), required=False)
# A `ConfigParam` group tagged as mutually-exclusive alternatives would replace
# the two separate params above once the framework supports that widget concept
# (see issue #6561 for discussion).  For now, listing both is a valid prototype.


@final
class Source(BaseSource):
    TITLE = "Stirling"
    DESCRIPTION = "Source for Stirling."
    URL = "https://www.stirling.wa.gov.au"
    COUNTRY = "au"
    CODEOWNERS = ["@markvp"]
    API_URL = "https://www.stirling.wa.gov.au/bincollectioncheck/getresult"

    TEST_CASES = {
        "by_address": {"address": "100 Cedric Street, Stirling, WA, Australia"},
        "by_coords": {"lat": -31.9034183, "lon": 115.8320855},
        "by_coords_str": {"lat": "-31.8783052", "lon": "115.8157741"},
    }

    # TODO(arch): once the framework supports mutually-exclusive PARAMS groups,
    # this becomes: PARAMS = [address_or_coords("address", "lat", "lon")]
    PARAMS = [_PARAMS_ADDRESS, _PARAMS_COORDS]

    HOWTO = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '100 Cedric Street, Stirling, WA, Australia'), "
            "or provide latitude and longitude coordinates."
        ),
    }

    parse = parsers.JsonParser(shape=ResponseShape)

    transformer = KeyValueTransformer(
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
        super().__init__(address=address, lat=lat, lon=lon)
        self._address = address
        self._lat = float(lat) if lat is not None else None
        self._lon = float(lon) if lon is not None else None

        if not self._address and (self._lat is None or self._lon is None):
            raise SourceArgumentNotFound(
                "address",
                "Either 'address' or both 'lat' and 'lon' must be provided.",
            )

    def _resolve_coordinates(self) -> tuple[float, float]:
        if self._lat is not None and self._lon is not None:
            return self._lat, self._lon
        # __init__ guarantees address is set when coords are not provided.
        address = self._address or ""
        try:
            location = geocode(address)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", address) from e
        return location["y"], location["x"]

    def retrieve(self, source):
        lat, lon = self._resolve_coordinates()
        self._headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "configid": "7c833520-7b62-4228-8522-fb1a220b32e8",
            "form": "57753bab-f589-44d7-8934-098b6d5c572f",
            "fields": f"{lon},{lat}",
            "apikeylookup": "Bin Day",
            "Origin": self.URL,
            "Referer": (
                f"{self.URL}/waste-and-environment/waste-and-recycling/bin-collections"
            ),
        }
        return retrievers.http_get(self)
