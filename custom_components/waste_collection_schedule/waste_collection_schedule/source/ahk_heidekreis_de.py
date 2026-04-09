import json
import logging
from datetime import datetime, timedelta, timezone

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

_LOGGER = logging.getLogger(__name__)

TITLE = "AHK Heidekreis"
DESCRIPTION = "Source for Abfallwirtschaft Heidekreis."
URL = "https://www.ahk-heidekreis.de/"
TEST_CASES = {
    "Munster - Wagnerstr. 10-18": {
        "city": "Munster",
        "postcode": "29633",
        "street": "Wagnerstr.",
        "house_number": "10-18",
    },
    "Fallingbostel - Konrad-Zuse-Str. 4": {
        "city": "Fallingbostel/Bad Fallingbostel",
        "postcode": 29683,
        "street": "Konrad-Zuse-Str.",
        "house_number": 4,
    },
}

# Field name mappings to support multiple API response formats.
# The API may return field names in different conventions depending on server version.
_STREET_NAME_KEYS = ("strassenName", "name", "Name", "streetName", "StreetName")
_STREET_PLZ_KEYS = ("plz", "PLZ", "Plz", "postalCode", "PostalCode")
_STREET_PLACE_KEYS = ("ort", "place", "Ort", "Place", "city", "City")
_STREET_ID_KEYS = ("id", "Id", "streetId", "StreetId", "strassenId")
_HOUSE_NR_KEYS = ("houseNr", "HouseNr", "hausnummer", "Hausnummer")
_HOUSE_NR_ADD_KEYS = (
    "houseNrAdd",
    "HouseNrAdd",
    "hausnummerZusatz",
    "HausnummerZusatz",
)
_OBJECT_ID_KEYS = (
    "idObject",
    "IdObject",
    "objektId",
    "ObjektId",
    "objectId",
    "ObjectId",
)

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "postcode": "PLZ",
        "house_number": "Hausnummer",
    }
}


def _get_field(item: dict, *possible_keys: str):
    """Return the value for the first matching key found in item."""
    for key in possible_keys:
        if key in item:
            return item[key]
    return None


class Source:
    def __init__(self, city, postcode, street, house_number):
        self._city = city
        self._postcode = str(postcode)
        self._street = street
        self._house_number = str(house_number)
        self._ics = ICS()

    def fetch(self):
        params = {
            "PartialName": self._street,
        }

        # get list of streets and house numbers
        r = requests.get(
            "https://ahkwebapi.heidekreis.de/api/QMasterData/QStreetByPartialName",
            params=params,
        )

        data = json.loads(r.text)
        if len(data) == 0:
            raise SourceArgumentNotFound("street", self._street)

        # Detect API field names from the first item and log for debugging
        if data:
            _LOGGER.debug(
                "QStreetByPartialName response keys: %s", list(data[0].keys())
            )

        street_entry = next(
            (
                item
                for item in data
                if _get_field(item, *_STREET_NAME_KEYS) == self._street
                and _get_field(item, *_STREET_PLZ_KEYS) == self._postcode
                and _get_field(item, *_STREET_PLACE_KEYS) == self._city
            ),
            None,
        )

        if street_entry is None:
            suggestions = [
                _get_field(item, *_STREET_NAME_KEYS)
                for item in data
                if _get_field(item, *_STREET_PLZ_KEYS) == self._postcode
                and _get_field(item, *_STREET_PLACE_KEYS) == self._city
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions=[s for s in suggestions if s]
            )

        street_id = _get_field(street_entry, *_STREET_ID_KEYS)
        if street_id is None:
            _LOGGER.error(
                "Unexpected API response format for street ID. Available keys: %s",
                list(street_entry.keys()),
            )
            raise SourceArgumentNotFound("street", self._street)
        params = {"StreetId": street_id}
        r = requests.get(
            "https://ahkwebapi.heidekreis.de/api/QMasterData/QHouseNrEkal",
            params=params,
        )
        r.raise_for_status()

        data = json.loads(r.text)
        if len(data) == 0:
            raise SourceArgumentNotFound("house_number", self._house_number)

        # Detect house number API field names and log for debugging
        if data:
            _LOGGER.debug("QHouseNrEkal response keys: %s", list(data[0].keys()))

        house_number_entry = next(
            (
                item
                for item in data
                if _get_field(item, *_HOUSE_NR_KEYS) is not None
                and _get_field(item, *_HOUSE_NR_ADD_KEYS) is not None
                and f"{_get_field(item, *_HOUSE_NR_KEYS)}{_get_field(item, *_HOUSE_NR_ADD_KEYS)}"
                == self._house_number
            ),
            None,
        )

        if house_number_entry is None:
            suggestions = [
                f"{_get_field(item, *_HOUSE_NR_KEYS)}{_get_field(item, *_HOUSE_NR_ADD_KEYS)}"
                for item in data
                if _get_field(item, *_HOUSE_NR_KEYS) is not None
                and _get_field(item, *_HOUSE_NR_ADD_KEYS) is not None
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, suggestions=suggestions
            )

        # get ics file
        object_id = _get_field(house_number_entry, *_OBJECT_ID_KEYS)
        if object_id is None:
            _LOGGER.error(
                "Unexpected API response format for object ID. Available keys: %s",
                list(house_number_entry.keys()),
            )
            raise SourceArgumentNotFound("house_number", self._house_number)
        params = {
            "von": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            + "Z",
            "bis": (datetime.now(timezone.utc) + timedelta(days=365)).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )[:-3]
            + "Z",
            "benachrichtigungVorJederAbholung": False,
            "abholbenachrichtigungTageVorher": 1,
            "abholbenachrichtigungUhrzeit": {
                "ticks": 28800000,
                "sekunden": 28800,
                "minuten": 480,
                "stunden": 8,
            },
            "benachrichtigungNächsterKalender": False,
            "kalenderBenachrichtigungTageVorEnde": 3,
            "kalenderbenachrichtigungUhrzeit": {
                "ticks": 28800000,
                "sekunden": 28800,
                "minuten": 480,
                "stunden": 8,
            },
        }
        headers = {"content-type": "application/json"}

        r = requests.post(
            f"https://ahkwebapi.heidekreis.de/api/object/{object_id}/QDisposalScheduler/asIcal",
            data=json.dumps(params),
            headers=headers,
        )
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            for bin_type in d[1].removesuffix(", ").split(", "):
                _LOGGER.info("%s - %s", d[0], d[1])
                entries.append(Collection(d[0], bin_type))
        return entries
