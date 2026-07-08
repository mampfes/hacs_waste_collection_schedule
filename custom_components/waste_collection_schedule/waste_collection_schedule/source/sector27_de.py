import datetime
import json
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Sector 27 - Datteln, Marl, Oer-Erkenschwick"
DESCRIPTION = "Source for Muellkalender in Kreis RE."
URL = "https://muellkalender.sector27.de"
TEST_CASES = {
    "Datteln": {"city": "Datteln", "street": "Am Bahnhof"},
    "Datteln Im Overkamp": {"city": "Datteln", "street": "Im Overkamp"},
    "Datteln range street": {
        "city": "Datteln",
        "street": "Ahsener Straße 113 - 161 (ungerade)",
    },
    "Marl": {"city": "Marl", "street": "Ahornweg"},
    "Oer-Erkenschick": {"city": "Oer-Erkenschwick", "street": "An der Zechenbahn"},
}

CITIES = {
    "Datteln": {"idCity": 9, "licenseKey": "DTTLN20137REKE382EHSE"},
    "Marl": {"idCity": 3, "licenseKey": "MRL3102HBBUHENWIP"},
    "Oer-Erkenschwick": {"idCity": 8, "licenseKey": "OSC1115KREHDFESEK"},
}

HEADERS = {"user-agent": "Mozilla/5.0"}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
    },
}


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street

    def getviewYearRange(self):
        yRange = []

        now = datetime.datetime.now()

        month = now.month
        year = now.year

        d = datetime.datetime(year, 1, 1, hour=12)

        yRange.append(int(datetime.datetime.timestamp(d)))

        # in november & december always fetch next year also
        if month > 8:
            d = datetime.datetime(year + 1, 1, 1, hour=12)
            yRange.append(int(datetime.datetime.timestamp(d)))

        return yRange

    def _lookup_street_id(self, city):
        """Resolve a street name to its sector27 street id.

        The upstream ``searchForStreets`` endpoint appears to truncate the
        result list after a handful of matches, so searching with the first
        whitespace-separated token of the street name fails when the street
        starts with a generic German article/preposition such as ``Im``,
        ``Am``, ``An``, ``Auf``, ``Zum`` and the distinctive word is the
        second one (e.g. ``"Im Overkamp"``).

        To be robust we try each distinct token of the configured street and
        look for an exact, case-insensitive, whitespace-stripped match in
        any of the responses. The first match wins. Only if no token yields
        a match do we surface a ``SourceArgumentNotFound(WithSuggestions)``
        error.
        """
        if not self._street:
            raise SourceArgumentNotFound("street", self._street)

        target = self._street.strip().casefold()
        # Preserve first-occurrence order while dropping duplicates.
        tokens: list[str] = []
        for token in self._street.split():
            if token and token not in tokens:
                tokens.append(token)

        suggestions: dict[str, None] = {}

        for token in tokens:
            params = {
                "idCity": city["idCity"],
                "licenseKey": city["licenseKey"],
                "searchFor": token,
            }
            r = requests.get(
                "https://muellkalender.sector27.de/web/searchForStreets",
                params=params,
                headers=HEADERS,
            )
            r.raise_for_status()
            entries = json.loads(extractJson(r.text))

            for entry in entries:
                name = entry.get("name", "").strip()
                if not name:
                    continue
                suggestions[name] = None
                if name.casefold() == target:
                    return entry["id"]

        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, list(suggestions.keys())
            )
        raise SourceArgumentNotFound("street", self._street)

    def fetch(self):
        city = CITIES.get(self._city)
        if city is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(CITIES.keys())
            )

        street_id = self._lookup_street_id(city)

        args = {
            "licenseKey": city["licenseKey"],
            "cityId": city["idCity"],
            "streetId": street_id,
            "viewrange": "yearRange",
        }

        entries = []

        for dt in self.getviewYearRange():
            args["viewdate"] = dt

            r = requests.get(
                "https://muellkalender.sector27.de/web/fetchPickups",
                params=args,
                headers=HEADERS,
            )
            r.raise_for_status()
            data = json.loads(extractJson(r.text))

            for ts, pickups in data["pickups"].items():
                for pickup in pickups:
                    type = pickup["label"]
                    pickupdate = datetime.date.fromtimestamp(int(ts))
                    entries.append(Collection(pickupdate, type))

        return entries


def extractJson(text):
    m = re.fullmatch(r"callbackFunc\((.*)\);", text)
    return m.group(1) if m else text
