import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Mecklenburgische Seenplatte"
DESCRIPTION = "Source for Landkreis Mecklenburgische Seenplatte waste collection."
URL = "https://www.lk-mecklenburgische-seenplatte.de"
COUNTRY = "de"
TEST_CASES = {
    "Atelierstraße (Neubrandenburg)": {
        "city": "Neubrandenburg",
        "street": "Atelierstraße",
    },
    "Dargun": {"city": "Dargun", "street": "Dargun"},
    "Ahornweg (Altentreptow)": {"city": "Altentreptow", "street": "Ahornweg"},
}

CALENDAR_URL = "https://www.lk-mecklenburgische-seenplatte.de/Abfallkalender"
AUTOCOMPLETE_URL = (
    "https://www.lk-mecklenburgische-seenplatte.de/output/autocomplete.php"
)
DOWNLOAD_URL = "https://www.lk-mecklenburgische-seenplatte.de/output/options.php"

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
    },
    "en": {
        "city": "City",
        "street": "Street",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Name of the municipality (as shown in the dropdown on the Abfallkalender page).",
        "street": "Street or district name. For entries shown with parentheses (e.g. 'Dargun (Dargun)') use only the part before the parenthesis (e.g. 'Dargun').",
    },
    "de": {
        "city": "Name der Gemeinde (wie im Dropdown auf der Abfallkalender-Seite angezeigt).",
        "street": "Straßen- oder Ortsteilname. Bei Einträgen mit Klammern (z.B. 'Dargun (Dargun)') nur den Teil vor der Klammer verwenden (z.B. 'Dargun').",
    },
}


class Source:
    def __init__(self, city: str, street: str):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        # Step 1: Fetch the calendar page and parse the city dropdown
        r = requests.get(CALENDAR_URL)
        if not r.ok:
            raise Exception(f"Error: failed to fetch url: {CALENDAR_URL}")

        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", id="sf_locid")
        if not select:
            raise Exception("Could not find city dropdown on calendar page")

        options = {
            o.string: o["value"]
            for o in select.find_all("option")
            if o.get("value") and o.string
        }

        if self._city not in options:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(options.keys())
            )

        refid = options[self._city]

        # Step 2: Query the autocomplete endpoint to find the street/district pois ID
        r = requests.get(
            AUTOCOMPLETE_URL,
            params={
                "out": "json",
                "type": "abto",
                "mode": "",
                "select": "2",
                "refid": refid,
                "term": self._street,
            },
        )
        if not r.ok:
            raise Exception(f"Error: failed to fetch url: {r.request.url}")

        # The API returns JSON null for search terms containing parentheses
        data = r.json() or []

        matches = [item for item in data if self._street in item[1]]
        if not matches:
            # Fetch all streets for suggestions
            r_all = requests.get(
                AUTOCOMPLETE_URL,
                params={
                    "out": "json",
                    "type": "abto",
                    "mode": "",
                    "select": "2",
                    "refid": refid,
                    "term": "",
                },
            )
            all_streets = [item[1] for item in (r_all.json() or [])]
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, all_streets
            )

        pois_id = matches[0][0]

        # Step 3: Download and parse the ICS calendar
        r = requests.get(
            DOWNLOAD_URL,
            params={
                "ModID": "48",
                "call": "ical",
                "pois": pois_id,
            },
        )
        if not r.ok:
            raise Exception(f"Error: failed to fetch url: {r.request.url}")

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
