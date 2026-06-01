from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "City of Albany"
DESCRIPTION = "Source for City of Albany, Western Australia waste collection."
URL = "https://www.albany.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Laithwood Circuit Marbelup (Zone A)": {
        "address": "Laithwood Circuit, Marbelup, Albany WA 6330"
    },
    "15 Melville Street Albany (Zone B)": {
        "address": "15 Melville Street, Albany WA 6330"
    },
}

ICON_MAP = {
    "General Waste & FOGO": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the City of Albany (e.g. '15 Melville Street, Albany WA 6330')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

LAYERS = [
    {
        "url": "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Trash_Pickup_A/FeatureServer/0",
        "waste_type": "General Waste & FOGO",
        "anchor": date(2021, 6, 28),
    },
    {
        "url": "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Trash_Pickup_B/FeatureServer/0",
        "waste_type": "General Waste & FOGO",
        "anchor": date(2021, 6, 21),
    },
    {
        "url": "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Recycling_Pickup_A/FeatureServer/0",
        "waste_type": "Recycling",
        "anchor": date(2021, 6, 21),
    },
    {
        "url": "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Recycling_Pickup_B/FeatureServer/0",
        "waste_type": "Recycling",
        "anchor": date(2021, 6, 28),
    },
]

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        for layer in LAYERS:
            try:
                features = query_feature_layer(layer["url"], geometry=location)
            except ArcGisError:
                continue

            attrs = features[0]
            day_name = next(
                (k for k in WEEKDAYS if str(attrs.get(k, "")).upper() == "YES"),
                None,
            )
            if day_name is None:
                continue

            day_of_week = WEEKDAYS[day_name]
            dates = self._fortnightly_dates(layer["anchor"], day_of_week)
            icon = ICON_MAP.get(layer["waste_type"])
            entries.extend(
                Collection(date=d, t=layer["waste_type"], icon=icon) for d in dates
            )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    @staticmethod
    def _fortnightly_dates(
        anchor: date, day_of_week: int, count: int = 13
    ) -> list[date]:
        week_monday = anchor - timedelta(days=anchor.weekday())
        first = week_monday + timedelta(days=day_of_week)
        today = date.today()
        d = first
        while d < today:
            d += timedelta(days=14)
        return [d + timedelta(days=14 * i) for i in range(count)]
