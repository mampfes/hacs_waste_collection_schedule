from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Moreton Bay"
DESCRIPTION = "Source for City of Moreton Bay, Queensland, Australia."
URL = "https://www.moretonbay.qld.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "25 Pumicestone Street, Bellara": {
        "house_number": "25",
        "street_name": "Pumicestone",
        "suburb": "Bellara",
    },
    "74 North Street, Woorim": {
        "house_number": 74,
        "street_name": "North Street",
        "suburb": "Woorim",
    },
    "8 Irene Street, Redcliffe": {
        "house_number": "8",
        "street_name": "Irene",
        "suburb": "Redcliffe",
    },
}

SOURCE_CODEOWNERS = ["@CRZTFR"]

PARAM_TRANSLATIONS = {
    "en": {
        "house_number": "House number",
        "street_name": "Street name",
        "suburb": "Suburb",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "house_number": "The house/unit number, e.g. '25'",
        "street_name": "The street name, e.g. 'Pumicestone' or 'Pumicestone Street'",
        "suburb": "The suburb, e.g. 'Bellara'",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your house number, street name and suburb exactly as they "
        "appear on the City of Moreton Bay bin-day lookup at "
        "https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days. "
        "The street name may be given with or without its street type "
        "(e.g. 'Pumicestone' or 'Pumicestone Street')."
    ),
}

# Public ArcGIS feature layer published on the City of Moreton Bay open-data
# portal (datahub.moretonbay.qld.gov.au → "Property Waste Collection Days and
# Recycle Weeks"). Each property parcel carries its collection weekday
# (Bin_Day) and its recycling fortnight (Recycle_Week = "WEEK 1"/"WEEK 2").
API_URL = (
    "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/"
    "MBRC_Waste/FeatureServer/0/query"
)

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Organics": Icons.GARDEN,
}

_WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

# Monday that starts a council "WEEK 1" recycling fortnight. Anchored to the
# council bin-day lookup: a WEEK 1 property (25 Pumicestone Street, Bellara)
# has its recycling collected Thu 16 Jul 2026, so the week of Mon 13 Jul 2026
# is WEEK 1. Queensland does not observe daylight saving, so this fixed
# fortnight parity stays correct all year. _week1_offset(d) == 0 means d falls
# in a council "WEEK 1"; == 1 means "WEEK 2".
WEEK1_REFERENCE = date(2026, 7, 13)

_WEEKS_AHEAD = 12  # how many weekly general-waste events to emit


def _week1_offset(d: date) -> int:
    return ((d - WEEK1_REFERENCE).days // 7) % 2


def _next_weekday(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7)


class Source:
    def __init__(self, house_number, street_name: str, suburb: str):
        self._house_number = str(house_number).strip()
        self._street_name = street_name.strip().upper()
        self._suburb = suburb.strip().upper()

    def _query(self) -> list[dict]:
        # Escape single quotes to keep the ArcGIS WHERE clause well-formed.
        house = self._house_number.replace("'", "''")
        street = self._street_name.replace("'", "''")
        suburb = self._suburb.replace("'", "''")
        where = (
            f"House_No='{house}' "
            f"AND UPPER(Road) LIKE '%{street}%' "
            f"AND UPPER(Suburb)='{suburb}'"
        )
        params = {
            "where": where,
            "outFields": "ADDRESS,Bin_Day,Recycle_Week",
            "returnGeometry": "false",
            "f": "json",
        }
        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        return [f["attributes"] for f in r.json().get("features", [])]

    def fetch(self) -> list[Collection]:
        features = self._query()

        if not features:
            # Offer nearby house numbers on the same street/suburb as hints.
            suggestions = self._suggestions()
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number",
                self._house_number,
                suggestions,
            )

        attrs = features[0]
        bin_day = (attrs.get("Bin_Day") or "").strip().upper()
        recycle_week = (attrs.get("Recycle_Week") or "").strip().upper()

        weekday = _WEEKDAYS.get(bin_day)
        if weekday is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, []
            )

        today = date.today()
        entries: list[Collection] = []

        # General waste: weekly on the collection weekday.
        d = _next_weekday(today, weekday)
        for _ in range(_WEEKS_AHEAD):
            entries.append(Collection(d, "General Waste", ICON_MAP["General Waste"]))
            d += timedelta(weeks=1)

        # Recycling: fortnightly on the collection weekday, in the property's
        # recycle week. Garden organics is fortnightly on the opposite week.
        recycle_offset = 0 if recycle_week == "WEEK 1" else 1
        garden_offset = 1 - recycle_offset

        for name, offset in (
            ("Recycling", recycle_offset),
            ("Garden Organics", garden_offset),
        ):
            d = _next_weekday(today, weekday)
            if _week1_offset(d) != offset:
                d += timedelta(weeks=1)
            for _ in range(_WEEKS_AHEAD // 2):
                entries.append(Collection(d, name, ICON_MAP[name]))
                d += timedelta(weeks=2)

        return entries

    def _suggestions(self) -> list[str]:
        street = self._street_name.replace("'", "''")
        suburb = self._suburb.replace("'", "''")
        params = {
            "where": (f"UPPER(Road) LIKE '%{street}%' AND UPPER(Suburb)='{suburb}'"),
            "outFields": "ADDRESS",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "f": "json",
        }
        try:
            r = requests.get(API_URL, params=params, timeout=30)
            r.raise_for_status()
            return [
                f["attributes"]["ADDRESS"]
                for f in r.json().get("features", [])
                if f["attributes"].get("ADDRESS")
            ][:10]
        except requests.RequestException:
            return []
