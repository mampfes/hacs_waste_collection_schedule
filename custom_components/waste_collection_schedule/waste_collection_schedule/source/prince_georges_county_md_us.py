from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Prince George's County, MD"
DESCRIPTION = (
    "Source for Prince George's County, Maryland curbside trash, recycling, "
    "bulky trash, and yard trim collection."
)
URL = "https://www.princegeorgescountymd.gov/departments-offices/environment/waste-recycling/residential-collections"
COUNTRY = "us"

TEST_CASES = {
    "6807 McCormick Rd, Upper Marlboro": {
        "address": "6807 McCormick Rd, Upper Marlboro, MD"
    },
    "2607 Haney Ave, Suitland": {"address": "2607 Haney Ave, Suitland, MD"},
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Bulky Trash": Icons.BULKY,
    "Yard Trim": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '1301 McCormick Dr, Upper Marlboro, MD')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# Prince George's County Department of the Environment "Once-A-Week"
# residential collection lookup layer. This is the same FeatureLayer that
# backs the County's own public "Waste Collection Services" address tool
# linked from the Residential Collections page (URL above).
TRASH_LAYER_URL = (
    "https://gisent.princegeorgescountymd.gov/gisonline/rest/services/"
    "DoE/RRD_PROP_TRASH/MapServer/0"
)

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

WEEKS_AHEAD = 26

# Fields on the layer that hold a weekly day-of-service name. The
# Wood-and-Tree-Debris field is intentionally excluded because it is always
# "Call 311 to Schedule" (an on-demand service, not a recurring weekly
# pickup), and there is no reliable "day" to project forward.
DAY_FIELDS = {
    "Trash_Day_of_Service1": "Trash",
    "Trash_Day_of_Service2": "Trash",
    "Recycle_Day_of_Service": "Recycling",
    "Bulky_Day_of_Service": "Bulky Trash",
    "Yard_Day_of_Service": "Yard Trim",
}

OUT_FIELDS = ",".join({*DAY_FIELDS, "Address"})


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        try:
            features = query_feature_layer(
                TRASH_LAYER_URL,
                geometry=location,
                out_fields=OUT_FIELDS,
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = self._select_feature(features)

        entries: list[Collection] = []
        seen_days: dict[str, set[str]] = {}
        for field, waste_type in DAY_FIELDS.items():
            day_name = (attrs.get(field) or "").strip().title()
            if day_name not in WEEKDAYS:
                continue
            # Avoid duplicate weekly entries when Trash_Day_of_Service1 and
            # Trash_Day_of_Service2 happen to name the same weekday.
            seen = seen_days.setdefault(waste_type, set())
            if day_name in seen:
                continue
            seen.add(day_name)
            entries += self._weekly_dates(day_name, waste_type)

        if not entries:
            # The property was found but is not enrolled in any
            # County-collected waste service (e.g. commercial/private-hauler
            # address), so there is nothing meaningful to report.
            raise SourceArgumentNotFound("address", self._address)

        return entries

    def _select_feature(self, features: list[dict]) -> dict:
        # A point that falls exactly on a shared parcel-boundary vertex can
        # intersect more than one polygon. Prefer the feature whose Address
        # starts with the same house number as the requested address.
        house_number = "".join(
            ch for ch in self._address.split()[0] if ch.isdigit()
        ).lstrip("0")
        if house_number:
            for attrs in features:
                found_address = (attrs.get("Address") or "").strip()
                found_house_number = found_address.split(" ")[0].lstrip("0")
                if found_house_number == house_number:
                    return attrs
        return features[0]

    @staticmethod
    def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS[day_name]
        today = date.today()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
            for i in range(WEEKS_AHEAD)
        ]
