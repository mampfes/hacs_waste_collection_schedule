import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Irado"
DESCRIPTION = (
    "Source for Irado waste collection services, covering Vlaardingen, Schiedam, "
    "Maassluis, Capelle aan den IJssel and Voorne aan Zee (Netherlands)."
)
URL = "https://www.irado.nl"
COUNTRY = "nl"
TEST_CASES = {
    "Zwanensingel_no_suffix": {"postcode": "3136GZ", "house_number": "7"},
    "Platanendreef_with_suffix": {
        "postcode": "3137CN",
        "house_number": "2",
        "suffix": "A",
    },
}

ICON_MAP = {
    "gft": Icons.BIO_KITCHEN,
    "papier": Icons.PAPER,
    "pmd": Icons.PLASTIC_PACKAGING,
    "restafval": Icons.GENERAL_WASTE,
}

TYPE_MAP = {
    "gft": "GFT",
    "papier": "Oud papier",
    "pmd": "PMD",
    "restafval": "Restafval",
}

MONTHS_NL = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the postcode (e.g. 3131VX) and house number you would use at https://www.irado.nl/afvalkalender",
    "de": "Geben Sie die Postleitzahl (z. B. 3131VX) und die Hausnummer ein, die Sie auch auf https://www.irado.nl/afvalkalender verwenden würden",
    "fr": "Saisissez le code postal (par ex. 3131VX) et le numéro de maison que vous utiliseriez sur https://www.irado.nl/afvalkalender",
    "it": "Inserisci il CAP (ad es. 3131VX) e il numero civico che utilizzeresti su https://www.irado.nl/afvalkalender",
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "house_number": "House number",
        "suffix": "House number suffix",
    },
    "de": {
        "postcode": "Postleitzahl",
        "house_number": "Hausnummer",
        "suffix": "Hausnummerzusatz",
    },
    "fr": {
        "postcode": "Code postal",
        "house_number": "Numéro de maison",
        "suffix": "Complément de numéro",
    },
    "it": {
        "postcode": "CAP",
        "house_number": "Numero civico",
        "suffix": "Suffisso del numero civico",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Dutch postcode, e.g. 3131VX",
        "house_number": "House number, e.g. 3",
        "suffix": "Optional house number suffix/addition, e.g. A",
    },
    "de": {
        "postcode": "Niederländische Postleitzahl, z. B. 3131VX",
        "house_number": "Hausnummer, z. B. 3",
        "suffix": "Optionaler Hausnummerzusatz, z. B. A",
    },
    "fr": {
        "postcode": "Code postal néerlandais, par ex. 3131VX",
        "house_number": "Numéro de maison, par ex. 3",
        "suffix": "Complément de numéro de maison facultatif, par ex. A",
    },
    "it": {
        "postcode": "CAP olandese, ad es. 3131VX",
        "house_number": "Numero civico, ad es. 3",
        "suffix": "Suffisso opzionale del numero civico, ad es. A",
    },
}

API_URL = "https://www.irado.nl/afvalkalender"
POSTCODE_PATTERN = re.compile(r"^(\d{4})\s*([A-Za-z]{2})$")


class Source:
    def __init__(self, postcode: str, house_number: str, suffix: str = ""):
        match = POSTCODE_PATTERN.match(postcode.strip())
        if not match:
            raise SourceArgumentNotFound(
                "postcode",
                postcode,
                "postcode must consist of 4 digits followed by 2 letters, e.g. 3131VX",
            )
        self._zipcode = match.group(1)
        self._zipcode_suffix = match.group(2).upper()
        self._house_number = str(house_number).strip()
        self._suffix = (suffix or "").strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        r = session.post(
            API_URL,
            data={
                "appointment_zipcode": self._zipcode,
                "appointment_zipcode_suffix": self._zipcode_suffix,
                "appointment_housenumber": self._house_number,
                "appointment_housenumber_suffix": self._suffix,
                "wsa_calendar": "4498794404",
            },
        )
        r.raise_for_status()

        if "form-error-message" in r.text:
            raise SourceArgumentNotFound(
                "postcode/house_number",
                f"{self._zipcode}{self._zipcode_suffix} {self._house_number}{self._suffix}",
                "this combination of postcode and house number is not known by Irado. "
                "Please verify it at https://www.irado.nl/afvalkalender",
            )

        r_year = session.get(API_URL, params={"view": "year"})
        r_year.raise_for_status()

        soup = BeautifulSoup(r_year.text, "html.parser")

        entries: list[Collection] = []
        current_year: int | None = None
        for el in soup.select(".avk-year, .av-cal"):
            classes = el.get("class") or []
            if "avk-year" in classes:
                try:
                    current_year = int(el.get_text(strip=True))
                except ValueError:
                    current_year = None
                continue

            if current_year is None:
                continue

            header = el.find("div", class_="avk-cal-header")
            if not header:
                continue
            month = MONTHS_NL.get(header.get_text(strip=True).lower())
            if not month:
                continue

            for pickup in el.find_all("span", class_="pickup-day"):
                # Calendar grids pad the first/last week of a month with
                # "inactive" days belonging to the adjacent month. Those
                # adjacent days are rendered a second time (as "active")
                # in their own month's grid, so skip "inactive" cells here
                # to avoid double-counting the same collection.
                day_cell = pickup.find_parent("div", class_="day")
                if not day_cell or "active" not in (day_cell.get("class") or []):
                    continue

                d_number = pickup.find("span", class_="d-number")
                if not d_number:
                    continue
                try:
                    day = int(d_number.get_text(strip=True))
                except ValueError:
                    continue

                for part in pickup.find_all(
                    "div", class_=lambda c: bool(c) and "pickup-part-" in c
                ):
                    waste_type = None
                    for cls in part.get("class", []):
                        if cls.startswith("pickup-part-"):
                            waste_type = cls[len("pickup-part-") :]
                            break
                    if not waste_type:
                        continue

                    try:
                        date = datetime.date(current_year, month, day)
                    except ValueError:
                        continue

                    entries.append(
                        Collection(
                            date=date,
                            t=TYPE_MAP.get(waste_type, waste_type),
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
