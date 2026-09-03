from datetime import timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ArcGis import (
    epoch_ms_to_date,
    get_next_n_dates,
    most_recent_weekday,
)

TITLE = "City of Darebin"
DESCRIPTION = "Source for City of Darebin waste collection."
URL = "https://www.darebin.vic.gov.au/"
TEST_CASES = {
    "266 Gower Street PRESTON 3072": {
        "property_location": "266 Gower Street PRESTON 3072"
    },
    "23 EDWARDES STREET RESERVOIR 3073": {
        "property_location": "23 EDWARDES STREET RESERVOIR 3073"
    },
    # The shapes people type. The register holds none of them verbatim.
    "Comma separated with state": {
        "property_location": "266 Gower Street, Preston VIC 3072"
    },
    "Abbreviated street type": {"property_location": "266 Gower St Preston"},
}
API_URL = "https://services-ap1.arcgis.com/1WJBRkF3v1EEG5gz/arcgis/rest/services/Waste_Collection_Date3/FeatureServer/0/query"
_ARG = "property_location"

# EZI_ADDRESS is the Vicmap address string: upper case, no commas, street type
# spelled out, suburb then postcode ("266 GOWER STREET PRESTON 3072"). The
# query below is a prefix LIKE against it, so a comma, a "VIC", or an
# abbreviated street type matches nothing at all -- which is most of what
# visitors actually type.
_STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CL": "CLOSE",
    "CR": "CRESCENT",
    "CRES": "CRESCENT",
    "CT": "COURT",
    "DR": "DRIVE",
    "ESP": "ESPLANADE",
    "GDNS": "GARDENS",
    "GR": "GROVE",
    "GRV": "GROVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "PDE": "PARADE",
    "PL": "PLACE",
    "RD": "ROAD",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}
_STATES = {"VIC", "VICTORIA"}

# Enough to show the visitor which property they meant, without pulling the
# whole municipality back when someone searches for a bare street name.
_MAX_SUGGESTIONS = 10

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _normalise(value: str) -> str:
    """Upper case, drop commas and collapse whitespace."""
    return " ".join(value.upper().replace(",", " ").split())


def _register_form(value: str) -> str:
    """What the visitor typed, written the way EZI_ADDRESS holds it."""
    words = [_STREET_TYPES.get(word, word) for word in _normalise(value).split()]
    while words and words[-1] in _STATES:
        words.pop()
    return " ".join(words)


def _prefixes(value: str) -> list[str]:
    """Progressively shorter prefixes of the address, longest first.

    EZI_ADDRESS ends with the suburb and postcode, and a visitor who gets
    either of those slightly wrong (or omits them) would otherwise match
    nothing. Shortening the prefix recovers the match; the caller still has to
    decide what to do when more than one property comes back.
    """
    address = _register_form(value)
    words = address.split()
    candidates = [address]
    # Trailing postcode, then the suburb one word at a time, never past the
    # street number and street name.
    if words and words[-1].isdigit() and len(words[-1]) == 4:
        words = words[:-1]
        candidates.append(" ".join(words))
    while len(words) > 2:
        words = words[:-1]
        candidates.append(" ".join(words))
    return list(dict.fromkeys(c for c in candidates if c))


class Source:
    def __init__(self, property_location: str):
        self.property_location = property_location

    def _query(self, where: str, out_fields: str, **extra) -> list[dict]:
        params = {"where": where, "outFields": out_fields, "f": "json", **extra}
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        return r.json().get("features") or []

    def _resolve_object_id(self) -> int:
        wanted = _register_form(self.property_location)
        for prefix in _prefixes(self.property_location):
            # ArcGIS `where` is SQL-ish, so a quote in the address (O'Hea
            # Street) would otherwise end the literal early.
            escaped = prefix.replace("'", "''")
            features = self._query(
                f"UPPER(EZI_ADDRESS) LIKE '{escaped}%'",
                "EZI_ADDRESS,OBJECTID",
                resultRecordCount=_MAX_SUGGESTIONS + 1,
            )
            if not features:
                continue

            exact = [
                f
                for f in features
                if _normalise(f["attributes"]["EZI_ADDRESS"]) == wanted
            ]
            if len(exact) == 1:
                return exact[0]["attributes"]["OBJECTID"]
            if len(features) == 1:
                return features[0]["attributes"]["OBJECTID"]

            raise SourceArgAmbiguousWithSuggestions(
                _ARG,
                self.property_location,
                [f["attributes"]["EZI_ADDRESS"] for f in features[:_MAX_SUGGESTIONS]],
            )

        raise SourceArgumentNotFound(
            _ARG,
            self.property_location,
            "Darebin holds addresses as street number, street name, suburb and "
            "postcode, for example '266 Gower Street PRESTON 3072'.",
        )

    def fetch(self) -> list[Collection]:
        object_id = self._resolve_object_id()

        features = self._query(
            "1=1",
            "Collection_Day,Condition,EZI_ADDRESS,Green_Collection,"
            "Recycle_Collection,Street_Sweeping",
            objectIds=object_id,
        )
        if not features:
            raise SourceArgumentNotFound(
                _ARG,
                self.property_location,
                "Darebin found the address but holds no collection details for it.",
            )
        attributes = features[0]["attributes"]

        collection_day = attributes["Collection_Day"]

        next_collection_date = most_recent_weekday(WEEKDAY_MAP[collection_day])

        green_collection = epoch_ms_to_date(attributes["Green_Collection"])
        recycle_collection = epoch_ms_to_date(attributes["Recycle_Collection"])
        street_sweeping = epoch_ms_to_date(attributes["Street_Sweeping"])

        green_collection_dates = get_next_n_dates(
            green_collection, 26, timedelta(days=14)
        )
        recycle_collection_dates = get_next_n_dates(
            recycle_collection, 26, timedelta(days=14)
        )
        waste_collection_dates = get_next_n_dates(
            next_collection_date, 52, timedelta(days=7)
        )
        street_sweeping_dates = get_next_n_dates(street_sweeping, 1, timedelta(weeks=6))

        entries = []

        entries.extend(
            [
                Collection(date=collection_date, t="Green Waste", icon="mdi:leaf")
                for collection_date in green_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_date, t="Recycling", icon="mdi:recycle")
                for collection_date in recycle_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_day, t="Rubbish", icon="mdi:trash-can")
                for collection_day in waste_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_day, t="Street Sweeping", icon="mdi:broom")
                for collection_day in street_sweeping_dates
            ]
        )
        return entries
