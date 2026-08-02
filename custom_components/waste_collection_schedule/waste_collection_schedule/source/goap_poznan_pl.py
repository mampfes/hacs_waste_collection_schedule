import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "GOAP Poznań"
DESCRIPTION = (
    "Source for the waste collection calendar of GOAP (Związek Międzygminny "
    "Gospodarka Odpadami Aglomeracji Poznańskiej), covering municipalities in "
    "the Poznań agglomeration such as Murowana Goślina, Czerwonak, Swarzędz "
    "and others."
)
URL = "https://www.goap.poznan.pl/"
COUNTRY = "pl"

BASE_URL = "https://web.c-trace.de/zmgoappoznan-abfallkalender"
FORM_PATH = "kalendarzodpadow"

TEST_CASES = {
    "Huta Pusta 1": {
        "city": "HUTA PUSTA",
        "street": "HUTA PUSTA",
        "house_number": "1",
        "location_type": "Z",
        "building_type": "J",
    },
    "Murowana Goślina, Poznańska 17": {
        "city": "MUROWANA GOŚLINA",
        "street": "POZNAŃSKA",
        "house_number": "17",
    },
}

ICON_MAP = {
    "rest": Icons.GENERAL_WASTE,
    "glas": Icons.GLASS,
    "papier": Icons.PAPER,
    "plastik": Icons.PLASTIC_PACKAGING,
    "bio": Icons.ORGANIC,
    "sperr": Icons.BULKY,
}

WASTE_TYPE_NAMES = {
    "rest": "Odpady zmieszane",
    "glas": "Szkło",
    "papier": "Papier",
    "plastik": "Tworzywa sztuczne i metal",
    "bio": "Bioodpady",
    "sperr": "Odpady wielkogabarytowe",
}

LOCATION_TYPES = ("Z", "N", "M", "R")
BUILDING_TYPES = ("J", "W")

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City/village name exactly as used on the GOAP calendar "
        "(usually upper case), e.g. 'MUROWANA GOŚLINA'.",
        "street": "Street name exactly as used on the GOAP calendar (usually "
        "upper case). For villages without named streets this is often the "
        "same as the city.",
        "house_number": "House number, including any letter/slash suffix "
        "exactly as shown on the GOAP calendar (e.g. '5' or '5/A').",
        "location_type": "Optional, only needed if the address is ambiguous. "
        "One of: Z (inhabited), N (uninhabited), M (mixed), R (recreational).",
        "building_type": "Optional, only needed if the address is ambiguous. "
        "One of: J (single-family building), W (multi-family building).",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "house_number": "House Number",
        "location_type": "Location Type",
        "building_type": "Building Type",
    },
    "de": {
        "city": "Stadt",
        "street": "Straße",
        "house_number": "Hausnummer",
        "location_type": "Standorttyp",
        "building_type": "Gebäudetyp",
    },
}


class Source:
    def __init__(
        self,
        city: str,
        street: str,
        house_number: str,
        location_type: str = "",
        building_type: str = "",
    ):
        if not city:
            raise SourceArgumentRequired("city", "city is required")
        if not street:
            raise SourceArgumentRequired("street", "street is required")
        if not house_number:
            raise SourceArgumentRequired("house_number", "house_number is required")

        self._city = str(city).strip()
        self._street = str(street).strip()
        self._house_number = str(house_number).strip()

        location_type = str(location_type or "").strip().upper()
        if location_type and location_type not in LOCATION_TYPES:
            raise SourceArgumentNotFoundWithSuggestions(
                "location_type", location_type, suggestions=list(LOCATION_TYPES)
            )
        self._location_type = location_type

        building_type = str(building_type or "").strip().upper()
        if building_type and building_type not in BUILDING_TYPES:
            raise SourceArgumentNotFoundWithSuggestions(
                "building_type", building_type, suggestions=list(BUILDING_TYPES)
            )
        self._building_type = building_type

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # The site uses a cookieless, URL-embedded ASP.NET session id
        # ("(S(xxxxxxxxxxxxxxxxxxxxxxxx))"). Requesting the form page without
        # one redirects us to a URL that contains a freshly minted one.
        r = session.get(f"{BASE_URL}/{FORM_PATH}", allow_redirects=False, timeout=30)
        location = r.headers.get("location")
        if location:
            form_url = f"https://web.c-trace.de{location}"
        else:
            # Already contained a valid session id / was not redirected.
            form_url = f"{BASE_URL}/{FORM_PATH}"

        data = {
            "posted": "yes",
            "ort": self._city,
            "strasse": self._street,
            "hausnr": self._house_number,
            "objekttyp": self._location_type,
            "objekttyp2": self._building_type,
        }
        r = session.post(form_url, data=data, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        plaene = soup.find("div", id="plaene")

        entries: list[Collection] = []
        if plaene is not None:
            for plan in plaene.find_all("div", class_="plan"):
                classes = plan.get("class") or []
                waste_key = next(
                    (c for c in classes if c not in ("plan", "clear")), None
                )
                if not waste_key:
                    continue
                waste_name = WASTE_TYPE_NAMES.get(waste_key, waste_key.capitalize())
                icon = ICON_MAP.get(waste_key)
                for li in plan.find_all("li"):
                    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", li.get_text())
                    if not match:
                        continue
                    collection_date = datetime.strptime(
                        match.group(1), "%d.%m.%Y"
                    ).date()
                    entries.append(
                        Collection(date=collection_date, t=waste_name, icon=icon)
                    )

        if not entries:
            raise SourceArgumentNotFound(
                "house_number",
                self._house_number,
                "no schedule was found for this address. Double check that "
                "city/street match the GOAP calendar exactly (usually upper "
                "case), and try setting location_type/building_type if the "
                "address has more than one matching record.",
            )

        return entries
