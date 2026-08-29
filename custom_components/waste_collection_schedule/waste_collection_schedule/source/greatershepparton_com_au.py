import re
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "City of Greater Shepparton"
DESCRIPTION = "Source for City of Greater Shepparton waste collection."
URL = "https://greatershepparton.com.au"
COUNTRY = "au"

TEST_CASES = {
    "161 Welsford Street Shepparton": {
        "street_address": "161 Welsford Street, Shepparton"
    },
    "15 Main Road Arcadia": {"street_address": "15 Main Road, Arcadia"},
    "1-16 Lonsdale Square Kialla": {"street_address": "1-16 Lonsdale Square, Kialla"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Organics": Icons.ORGANIC,
    "Glass": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your full street address, e.g. '161 Welsford Street, Shepparton'. "
        "Use full street-type words (Street, Road, Square) rather than "
        "abbreviations (St, Rd, Sq) - the council's address lookup only "
        "matches on the full word."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street address within the City of Greater Shepparton",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street Address",
    },
}

SOURCE_CODEOWNERS = ["@RedPandaDoge"]

ADDRESS_API_URL = "https://greatershepparton.com.au/external/gis-api/address"
ZONE_FROM_LOCATION_API_URL = (
    "https://greatershepparton.com.au/external/gis-api/bin-zone-name-from-location"
)
ZONE_SCHEDULES_URL = (
    "https://greatershepparton.com.au/external/gis-api/bin-zone-schedules"
)

_REQUEST_TIMEOUT = 30

_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Every one of the council's 20 zones (Monday A .. Friday D) uses the same
# collection cadence per bin colour; only the per-zone reference dates differ,
# and those are fetched live from ZONE_SCHEDULES_URL on every call (see
# _extract_reference_dates below).
_BIN_INTERVAL_DAYS = {
    "General Waste": 14,
    "Recycling": 14,
    "Organics": 7,
    "Glass": 28,
}

# How many upcoming occurrences to return per bin type, chosen so every bin
# covers a comparable ~12-16 week horizon regardless of its cadence.
_OCCURRENCES_TO_RETURN = {
    "General Waste": 6,
    "Recycling": 6,
    "Organics": 12,
    "Glass": 4,
}

# JS variable holding each bin's reference date inside bin-zone-schedules'
# getZoneFromName(zoneName) switch statement.
_REFERENCE_DATE_VAR = {
    "General Waste": "redBinReferenceDate",
    "Recycling": "yellowBinReferenceDate",
    "Organics": "greenBinReferenceDate",
    "Glass": "purpleBinReferenceDate",
}

# NOTE ON SCOPE: bin-zone-schedules also encodes a temporary Christmas/New
# Year collection-day shift for some zones (wrapped in a "ChangingSchedule"
# conditional in the source JS). Which days-of-week are affected depends on
# which weekday the holidays fall on in a given year, and modelling it would
# require interpreting the JS control flow rather than just its date literals.
# This source therefore does not model that temporary window; collection dates
# may be off by up to a day for the ~2 weeks spanning Christmas/New Year.


def _normalise(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _geocode(street_address: str) -> tuple[float, float]:
    # The search endpoint silently returns zero results if the query
    # contains punctuation like commas, or repeated whitespace - normalise
    # both away before searching.
    search_query = re.sub(r"[,.]", " ", street_address)
    search_query = re.sub(r"\s+", " ", search_query).strip()
    response = requests.get(
        ADDRESS_API_URL,
        params={"search": search_query},
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    candidates = response.json()

    if not candidates:
        raise SourceArgumentNotFound("street_address", street_address)

    normalised_input = _normalise(street_address)
    matches = [
        c
        for c in candidates
        if _normalise(c["eziAddress"]).startswith(normalised_input)
    ]

    if len(matches) == 1:
        match = matches[0]
    elif len(candidates) == 1:
        match = candidates[0]
    else:
        suggestions = [c["eziAddress"] for c in (matches or candidates)]
        raise SourceArgAmbiguousWithSuggestions(
            "street_address", street_address, suggestions
        )

    return match["latitude"], match["longitude"]


def _get_zone_name(latitude: float, longitude: float, street_address: str) -> str:
    response = requests.get(
        ZONE_FROM_LOCATION_API_URL,
        params={"latitude": latitude, "longitude": longitude},
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    zone_name = response.json()
    if not isinstance(zone_name, str) or not zone_name:
        raise SourceArgumentNotFound("street_address", street_address)
    return zone_name


def _extract_reference_dates(schedule_js: str, zone_name: str) -> dict[str, date]:
    zone_block_match = re.search(
        r'case\s+"' + re.escape(zone_name) + r'"\s*:(.*?)(?=\n\s*case\s+"|default\s*:)',
        schedule_js,
        re.DOTALL,
    )
    if zone_block_match is None:
        raise ValueError(
            f"Could not locate zone '{zone_name}' in Greater Shepparton's "
            "bin-zone-schedules module - the site's data format may have changed."
        )
    zone_block = zone_block_match.group(1)

    day_name = zone_name.split(" ")[0]
    if day_name not in _WEEKDAYS:
        raise ValueError(
            f"Unexpected zone name format from Greater Shepparton: '{zone_name}'"
        )
    expected_weekday = _WEEKDAYS.index(day_name)

    reference_dates: dict[str, date] = {}
    for bin_type, var_name in _REFERENCE_DATE_VAR.items():
        date_match = re.search(
            var_name + r'\s*=.*?new Date\("(\d{4}-\d{2}-\d{2})T', zone_block
        )
        if date_match is None:
            raise ValueError(
                f"Could not find {var_name} for zone '{zone_name}' in Greater "
                "Shepparton's bin-zone-schedules module - the site's data "
                "format may have changed."
            )
        reference_date = date.fromisoformat(date_match.group(1))
        if reference_date.weekday() != expected_weekday:
            raise ValueError(
                f"Reference date for {bin_type} in zone '{zone_name}' "
                f"({reference_date}) does not fall on a {day_name} - Greater "
                "Shepparton's data format may have changed."
            )
        reference_dates[bin_type] = reference_date

    return reference_dates


def _next_occurrences(reference: date, interval_days: int, count: int) -> list[date]:
    today = date.today()
    days_since_reference = (today - reference).days
    if days_since_reference < 0:
        first = reference
    else:
        cycles_elapsed = days_since_reference // interval_days
        first = reference + timedelta(days=cycles_elapsed * interval_days)
        if first < today:
            first += timedelta(days=interval_days)
    return [first + timedelta(days=interval_days * i) for i in range(count)]


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        street_address = (self._street_address or "").strip()
        if not street_address:
            raise SourceArgumentRequired(
                "street_address",
                "a street address is required to look up your bin collection zone",
            )

        latitude, longitude = _geocode(street_address)
        zone_name = _get_zone_name(latitude, longitude, street_address)

        schedule_response = requests.get(ZONE_SCHEDULES_URL, timeout=_REQUEST_TIMEOUT)
        schedule_response.raise_for_status()
        reference_dates = _extract_reference_dates(schedule_response.text, zone_name)

        entries: list[Collection] = []
        for bin_type, reference_date in reference_dates.items():
            interval_days = _BIN_INTERVAL_DAYS[bin_type]
            occurrences = _next_occurrences(
                reference_date, interval_days, _OCCURRENCES_TO_RETURN[bin_type]
            )
            for collection_date in occurrences:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type),
                    )
                )

        return entries
