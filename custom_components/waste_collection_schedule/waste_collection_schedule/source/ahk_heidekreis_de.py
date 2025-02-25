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

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "postcode": "PLZ",
        "house_number": "Hausnummer",
    }
}


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

        street_entry = next(
            (
                item
                for item in data
                if item["name"] == self._street
                and item["plz"] == self._postcode
                and item["place"] == self._city
            ),
            None,
        )

        if street_entry is None:
            suggestions = [
                item["name"]
                for item in data
                if item["plz"] == self._postcode and item["place"] == self._city
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions=suggestions
            )

        params = {"StreetId": street_entry["id"]}
        r = requests.get(
            "https://ahkwebapi.heidekreis.de/api/QMasterData/QHouseNrEkal",
            params=params,
        )
        r.raise_for_status()

        data = json.loads(r.text)
        if len(data) == 0:
            raise SourceArgumentNotFound("house_number", self._house_number)

        house_number_entry = next(
            (
                item
                for item in data
                if f"{item['houseNr']}{item['houseNrAdd']}" == self._house_number
            ),
            None,
        )

        if house_number_entry is None:
            suggestions = [f"{item['houseNr']}{item['houseNrAdd']}" for item in data]
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, suggestions=suggestions
            )

        # get ics file
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
            f"https://ahkwebapi.heidekreis.de/api/object/{house_number_entry['idObject']}/QDisposalScheduler/asIcal",
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
