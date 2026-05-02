from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadtreinigung Gießen"
DESCRIPTION = "Source for Stadtreinigung Gießen waste collection schedule."
URL = "https://stadtreinigung.giessen.de"
TEST_CASES = {
    "Achstattring 1": {
        "street": "Achstattring",
        "house_number": "1",
    },
    "Berliner Platz 5": {
        "street": "Berliner Platz",
        "house_number": "5",
    },
    "Marktplatz 10": {
        "street": "Marktplatz",
        "house_number": "10",
    },
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
    "Astwerk": "mdi:tree",
    "Weihnachtsbaum": "mdi:pine-tree",
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
    "it": {
        "street": "Via",
        "house_number": "Numero civico",
    },
    "fr": {
        "street": "Rue",
        "house_number": "Numéro de maison",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Enter the street name. If not found, a dropdown with suggestions will appear.",
        "house_number": "House number",
    },
    "de": {
        "street": "Straßenname eingeben. Bei ungültiger Eingabe erscheint ein Dropdown mit Vorschlägen.",
        "house_number": "Hausnummer",
    },
    "it": {
        "street": "Inserire il nome della via. Se non trovata, apparirà un menu a tendina con suggerimenti.",
        "house_number": "Numero civico",
    },
    "fr": {
        "street": "Entrez le nom de la rue. Si non trouvée, une liste déroulante avec des suggestions apparaîtra.",
        "house_number": "Numéro de maison",
    },
}

BASE_URL = "https://stadtreinigung.giessen.de/akal/akal1.php"


class StreetOptionParser(HTMLParser):
    """Parse the street dropdown options from the HTML form."""

    def __init__(self):
        super().__init__()
        self._streets = {}  # {street_name: street_value}
        self._in_select = False
        self._current_value = None

    @property
    def streets(self):
        return self._streets

    def handle_starttag(self, tag, attrs):
        if tag == "select":
            d = dict(attrs)
            if d.get("name") == "strasse":
                self._in_select = True
        elif tag == "option" and self._in_select:
            d = dict(attrs)
            self._current_value = d.get("value")

    def handle_data(self, data):
        if self._in_select and self._current_value is not None:
            street_name = data.strip()
            if street_name:
                self._streets[street_name] = self._current_value
            self._current_value = None

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_select = False
        elif tag == "option":
            self._current_value = None


class Source:
    def __init__(self, street: str, house_number: str):
        self._street = street.strip()
        self._house_number = str(house_number).strip()
        self._ics = ICS()

    def _get_alphabet_range(self, letter: str) -> tuple[str, str]:
        """Get the 'von' and 'bis' parameters for the given letter."""
        letter = letter.upper()
        # 'bis' is the next letter in the alphabet
        if letter == "Z":
            # For Z, use [ which comes after Z in ASCII
            return (letter, "[")
        else:
            next_letter = chr(ord(letter) + 1)
            return (letter, next_letter)

    def _load_streets_for_letter(
        self, session: requests.Session, letter: str
    ) -> dict[str, str]:
        """Load all streets starting with the given letter."""
        von, bis = self._get_alphabet_range(letter)
        r = session.get(BASE_URL, params={"von": von, "bis": bis})
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = StreetOptionParser()
        parser.feed(r.text)
        return parser.streets

    def _find_street_value(self, session: requests.Session) -> tuple[str, str, str]:
        """Find the street value by searching through the alphabet pages.

        Returns:
            tuple: (street_value, von, bis) - the street ID and alphabet range params
        """
        first_letter = self._street[0].upper()
        streets = self._load_streets_for_letter(session, first_letter)
        von, bis = self._get_alphabet_range(first_letter)

        # Try to find exact match first
        if self._street in streets:
            return streets[self._street], von, bis

        # Try case-insensitive exact match
        street_lower = self._street.lower()
        for street_name, street_value in streets.items():
            if street_name.lower() == street_lower:
                return street_value, von, bis

        # Try partial match - collect all matches
        partial_matches = {
            name: value
            for name, value in streets.items()
            if street_lower in name.lower()
        }

        # If exactly one partial match, use it
        if len(partial_matches) == 1:
            street_name, street_value = next(iter(partial_matches.items()))
            return street_value, von, bis

        # If multiple partial matches, show them as suggestions
        if len(partial_matches) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                sorted(partial_matches.keys()),
            )

        # No match found - raise exception with all streets for this letter
        available_streets = sorted(streets.keys())
        raise SourceArgumentNotFoundWithSuggestions(
            "street",
            self._street,
            available_streets,
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Find the street value and the correct alphabet range
        street_value, von, bis = self._find_street_value(session)

        # Prepare POST data to download the iCalendar
        data = {
            "strasse": street_value,
            "hausnr": self._house_number,
            "ical": " iCalendar",  # The button value
        }

        # Send POST request to get the ICS file
        r = session.post(
            BASE_URL,
            params={"von": von, "bis": bis},
            data=data,
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        # Parse the ICS data
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            waste_type = d[1].strip()
            icon = None
            # Try to find an icon based on the waste type
            for key, value in ICON_MAP.items():
                if key.lower() in waste_type.lower():
                    icon = value
                    break
            entries.append(Collection(d[0], waste_type, icon=icon))

        return entries
