import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

_LOGGER = logging.getLogger(__name__)

TITLE = "Stadtreinigung Leipzig"
DESCRIPTION = "Source for Stadtreinigung Leipzig."
URL = "https://stadtreinigung-leipzig.de"
TEST_CASES = {"Bahnhofsallee": {"street": "Bahnhofsallee", "house_number": 7}}


class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = house_number
        self._ics = ICS()

    def fetch(self):
        # get list of streets and house numbers
        r = requests.get(
            "https://stadtreinigung-leipzig.de/rest/odata/Streets",
            params={"search": self._street},
        )
        r.raise_for_status()

        streets = json.loads(r.text).get("results") or []
        if len(streets) == 0:
            raise SourceArgumentNotFound("street", self._street)
        numbers = [
            number
            for entry in streets
            if entry.get("name") == self._street
            for number in entry.get("numbers") or []
        ]
        if not numbers:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, sorted({s.get("name") for s in streets})
            )

        # a house number can have several positions (e.g. one per bin type)
        position_nos = [
            position
            for number in numbers
            if str(number.get("number")) == str(self._house_number)
            for position in number.get("position_nos") or []
        ]
        if not position_nos:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number",
                self._house_number,
                [n.get("number") for n in numbers],
            )
        # get ics file, the calendar takes all positions comma-separated
        params = {
            "position_nos": ",".join(position_nos),
            "name": f"{self._street} {self._house_number}",
            "mode": "download",
        }
        r = requests.get(
            "https://stadtreinigung-leipzig.de/wir-kommen-zu-ihnen/abfallkalender/ical.ics",
            params=params,
        )
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1].removesuffix(", ")))
        return entries
