from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    get_next_n_dates,
    query_feature_layer,
)

TITLE = "Charleston County, SC"
DESCRIPTION = "Source for Charleston County, SC residential curbside recycling."
URL = (
    "https://www.charlestoncounty.org/departments/environmental-management/recycle.php"
)
COUNTRY = "us"

TEST_CASES = {
    "Downtown Charleston": {"address": "123 Coming St, Charleston, SC 29403"},
    "Johns Island": {"address": "2758 August Rd, Johns Island, SC 29455"},
}

SOURCE_CODEOWNERS = ["@dmkjr"]

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city, state, and ZIP code.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

FEATURE_URL = "https://services.arcgis.com/jR9eNCjAkxwH2nLe/arcgis/rest/services/Curbside_Recycling_Days/FeatureServer/0"
DATE_FORMAT = "%B %d"

# The county publishes only the next exact pickup date; recycling then
# recurs on a fixed biweekly cadence, so project that many further pickups.
PICKUPS_AHEAD = 13


def _parse_next_pickup(value: str) -> date:
    """Parse the yearless next-pickup date published by Charleston County."""
    today = date.today()
    parsed = datetime.strptime(value.strip(), DATE_FORMAT).date()
    pickup = parsed.replace(year=today.year)

    # A January pickup published in December belongs to the next calendar year.
    if pickup < today and (today - pickup).days > 30:
        pickup = pickup.replace(year=today.year + 1)

    # The layer is normally updated before each collection. If it is briefly
    # stale after a pickup, retain its official biweekly cadence.
    while pickup < today:
        pickup += timedelta(weeks=2)

    return pickup


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
            features = query_feature_layer(
                FEATURE_URL,
                geometry=location,
                out_fields="PickupDate",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        pickup_date = (features[0].get("PickupDate") or "").strip()
        if not pickup_date:
            raise SourceArgumentNotFound("address", self._address)

        try:
            next_pickup = _parse_next_pickup(pickup_date)
        except ValueError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        return [
            Collection(
                date=pickup,
                t="Recycling",
                icon=Icons.RECYCLING,
            )
            for pickup in get_next_n_dates(
                next_pickup, PICKUPS_AHEAD, timedelta(weeks=2)
            )
        ]
