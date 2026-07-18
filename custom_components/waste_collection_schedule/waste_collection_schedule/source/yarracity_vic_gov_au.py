from datetime import date, timedelta

from dateutil.easter import easter
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    get_next_n_dates,
    most_recent_weekday,
    query_feature_layer,
)

TITLE = "City of Yarra"
DESCRIPTION = "Source for City of Yarra waste collection."
URL = "https://www.yarracity.vic.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Fitzroy Town Hall": {"address": "201 Napier Street, Fitzroy VIC 3065"},
    "Richmond Town Hall": {"address": "333 Bridge Road, Richmond VIC 3121"},
}
SOURCE_CODEOWNERS = ["@yeaaaaaahh"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your full street address including suburb and postcode, "
        "e.g. '333 Bridge Road, Richmond VIC 3121'."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": (
            "Full street address within the City of Yarra, "
            "including suburb and postcode"
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Glass": Icons.GLASS,
    "FOGO": Icons.BIO_KITCHEN,
}

MAP_SERVER_URL = (
    "https://yccgis-prd.esriaustraliaonline.com.au/arcgis/rest/services/"
    "Waste_Services/CW_FC_PRD_Waste_Collection/MapServer"
)
GLASS_LAYER_URL = f"{MAP_SERVER_URL}/0"
WASTE_LAYER_URL = f"{MAP_SERVER_URL}/1"

WEEKS_AHEAD = 52

_WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _holiday_shift(d: date) -> date:
    # Council rule: collections run on all public holidays except Good Friday
    # and Christmas Day, when the collection happens one day later.
    if d == easter(d.year) - timedelta(days=2) or d == date(d.year, 12, 25):
        return d + timedelta(days=1)
    return d


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(f"{self._address}, Victoria, Australia")
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        try:
            waste = query_feature_layer(
                WASTE_LAYER_URL,
                geometry=location,
                out_fields="collection_day,recycling_anchor_date",
            )[0]
            glass = query_feature_layer(
                GLASS_LAYER_URL,
                geometry=location,
                out_fields="anchor_date,frequency_days",
            )[0]
        except ArcGisError as e:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "the address must be within the City of Yarra.",
            ) from e

        day_name = waste["collection_day"]
        if day_name not in _WEEKDAYS:
            raise ValueError(f"Unexpected collection day: {day_name!r}")

        entries = []

        # Rubbish and FOGO are collected weekly on the property's collection day.
        for d in get_next_n_dates(
            most_recent_weekday(_WEEKDAYS[day_name]), WEEKS_AHEAD, timedelta(days=7)
        ):
            d = _holiday_shift(d)
            entries.append(Collection(d, "Rubbish", ICON_MAP["Rubbish"]))
            entries.append(Collection(d, "FOGO", ICON_MAP["FOGO"]))

        # Recycling alternates fortnightly between zones; the layer's anchor
        # date fixes this property's phase. DateOnly fields are ISO strings.
        for d in get_next_n_dates(
            date.fromisoformat(waste["recycling_anchor_date"]),
            WEEKS_AHEAD // 2,
            timedelta(days=14),
        ):
            entries.append(
                Collection(_holiday_shift(d), "Recycling", ICON_MAP["Recycling"])
            )

        # Glass runs on its own cycle (currently every 28 days) with an
        # independent per-polygon anchor.
        for d in get_next_n_dates(
            date.fromisoformat(glass["anchor_date"]),
            WEEKS_AHEAD // 4,
            timedelta(days=int(glass["frequency_days"])),
        ):
            entries.append(Collection(_holiday_shift(d), "Glass", ICON_MAP["Glass"]))

        return entries
